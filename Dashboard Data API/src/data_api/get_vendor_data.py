from functools import cache
import sys
from threading import Condition, Lock

from cachetools import cached
from data_api.database.database_connection import sap_database_engine
import pandas as pd
from data_api.utils.caching import PURCHASING_TABLE_CACHE
from data_api.utils.environment_variables import VENDOR_DATA_CUSTOM_CONDITION
from data_api.utils.logging import logger


# Perform the relevant queries to populate the vendor tables
# TODO #74: simplify some of the query logic to avoid making so many queries

PRODUCT_TABLE_QUERY = """select a.CardCode, c.CardName, a.ItemCode, d.ItemName 
from OSPP a
inner join OCRD b on b.CardCode = a.CardCode
inner join OPOR c on c.CardCode = a.CardCode
inner join OITM d on d.ItemCode = a.ItemCode
where b.CardType = 'S'"""

# TODO #74: Account for business days in the run rate calculation
UNIT_SALES_TABLE_QUERY = f"""
select x.ItemCode, x.ItemName, x.Sales_180_day, x.DailyRunRate, x.InStock, x.WorkingDaysOnHand, x.OnOrder, x.MinInventoryLevel,
case
	when WorkingDaysOnHand < 65.1 then (65.1 - WorkingDaysOnHand) * DailyRunRate - OnOrder
	else 0
end [Order_for_90d_supply]
from
(select b.ItemCode, c.ItemName, sum(b.Quantity) [Sales_180_day], sum(b.Quantity)/(30.4*6) [DailyRunRate], d.OnHand - c.IsCommited [InStock], 
cast(((d.OnHand - c.IsCommited)/ nullif(sum(b.Quantity)/(30.4*6),0)) as numeric(10,2)) [WorkingDaysOnHand], c.OnOrder, c.MinLevel [MinInventoryLevel]

from OINV a
inner join INV1 b on b.DocEntry = a.DocEntry
inner join OITM c on c.ItemCode = b.ItemCode
inner join OITW d on d.ItemCode = c.ItemCode

where a.DocDate between DATEADD(month,-6,DATEADD(mm, DATEDIFF(mm,0,getdate()), 0)) and DATEADD(mm, DATEDIFF(mm,0,getdate()), 0) 
and {VENDOR_DATA_CUSTOM_CONDITION}

group by b.ItemCode, c.ItemName, d.OnHand, c.IsCommited, c.OnOrder, c.MinLevel) x"""

PURCHASE_ORDER_FREQUENCY_QUERY="""select a.CardCode, a.DocNum, a.DocDate [Order_date], b.ActDelDate [Reciept Date] 
from OPOR a
inner join PDN1 b on b.BaseDocNum = a.DocNum
where a.DocDate between DATEADD(month,-12,DATEADD(mm, DATEDIFF(mm,0,getdate()), 0)) and DATEADD(mm, DATEDIFF(mm,0,getdate()), 0)"""

USUAL_ORDER_TABLE_QUERY="""SELECT a.[ItemCode],a.Dscription [ItemName],  count(distinct b.[DocNum]) [Number_of_Orders], AVG(a.Quantity) [Avg_Ord]
FROM POR1 a  
INNER JOIN OPOR b ON a.DocEntry = b.DocEntry 
where 
--a.[ItemCode] = '750-1-72' and
b.DocDate between DATEADD(month,-6,DATEADD(mm, DATEDIFF(mm,0,getdate()), 0)) and DATEADD(mm, DATEDIFF(mm,0,getdate()), 0)
group by a.[ItemCode],a.Dscription"""

LAST_ORDER_TABLE_QUERY="""SELECT a.[ItemCode], MAX(b.DocDate) [Last_Order]
FROM POR1 a  
INNER JOIN OPOR b ON a.DocEntry = b.DocEntry 
group by a.[ItemCode]"""

HOLIDAYS_QUERY="""SELECT [HldCode],[StrDate],[EndDate]
  FROM HLD1
  WHERE [StrDate] = [EndDate]
"""

import datetime
import calendar

def days_to_end_of_month(date_obj):
    """
    Calculates the number of days remaining until the end of the month
    for a given date.

    Args:
        date_obj (datetime.date): The date for which to calculate the remaining days.

    Returns:
        int: The number of days remaining until the end of the month.
    """
    year = date_obj.year
    month = date_obj.month

    # Get the last day of the month
    last_day_of_month = calendar.monthrange(year, month)[1]

    # Calculate the remaining days
    remaining_days = last_day_of_month - date_obj.day
    return remaining_days

def order_quant_90(order_for_90d_supply):
    raise NotImplementedError() # TODO #74: Implement order quantity calculation for 90 days supply

def apply_filters(dataframe):
    #Remove discontinued items
    def is_discontinued(df):
        return df["ItemName"].str.contains("(DISCONTINUED)", regex=False)
    return dataframe[~is_discontinued(dataframe)]

# Port of logic from R

def get_purchasing_table():
    vendor_item_table = pd.read_sql(PRODUCT_TABLE_QUERY, sap_database_engine) \
        .drop_duplicates()
    unit_sales_table = pd.read_sql(UNIT_SALES_TABLE_QUERY, sap_database_engine) \
        .round(1)
    purchase_order_lead_time_table = pd.read_sql(PURCHASE_ORDER_FREQUENCY_QUERY, sap_database_engine)
    # calc avg lead time per product
    purchase_order_lead_time_table['Avg Lead Time'] = (purchase_order_lead_time_table['Reciept Date'] - purchase_order_lead_time_table['Order_date']).dt.days
    purchase_order_lead_time_table = purchase_order_lead_time_table.groupby('CardCode', as_index=False)['Avg Lead Time'] \
        .agg('mean') \
		.drop_duplicates() \
		.round(0)
    usual_order_table = pd.read_sql(USUAL_ORDER_TABLE_QUERY, sap_database_engine)
    last_order_table = pd.read_sql(LAST_ORDER_TABLE_QUERY, sap_database_engine)

    merged_table = vendor_item_table.merge(unit_sales_table, how='outer') \
        .merge(purchase_order_lead_time_table, how='left') \
        .merge(usual_order_table,how='outer') \
        .merge(last_order_table, how='left') \
        .loc[:,['CardCode', 'CardName', 'ItemCode', 'ItemName', 'WorkingDaysOnHand', 'OnOrder', 'InStock', 'DailyRunRate', 'MinInventoryLevel']]
    
    merged_table = apply_filters(merged_table)
    return merged_table


@cached(cache=PURCHASING_TABLE_CACHE,condition=Condition(Lock()))
def compute_vendor_data_table():
    logger.info("Generating vendor items purchased table...")
    table = get_purchasing_table()
    logger.debug(f"Generated table size: {sys.getsizeof(table)}")
    return table