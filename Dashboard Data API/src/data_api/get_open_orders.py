
from threading import Condition, Lock
from cachetools import cached
from data_api.database.database_connection import sap_database_engine
import pandas as pd
from data_api.utils.caching import RECENT_ORDERS_CACHE
from data_api.utils.logging import logger

ALL_ORDERS_QUERY="""SELECT a.[ItemCode], a.[Dscription] [ItemName], b.[CardCode] [VendorCode], b.[CardName], b.[DocDate] [OrderDate], b.DocDueDate [DueDate],a.[Quantity] [QuantityOrdered], a.[Price],  b.[DocNum] [PO_Num], 
c.ActDelDate [DeliveryDate],a.[LineStatus], c.InvQty [QuantityReceived], 
DATEDIFF(day,b.DocDueDate,case when c.ActDelDate is not null then c.ActDelDate 
							   when c.ActDelDate is null and a.LineStatus = 'o' and b.DocDueDate > getdate() then b.DocDueDate
							   when c.ActDelDate is null and a.LineStatus = 'o' and b.DocDueDate < getdate() then GETDATE()
							   end) [DaysOrderDelayed], b.Comments
FROM POR1 a  
INNER JOIN OPOR b ON a.DocEntry = b.DocEntry
full join PDN1 c on c.BaseDocNum = b.DocNum and c.ItemCode = a.ItemCode
WHERE b.DocDate >=  DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()) -1, 0) -- Selecting orders placed since first day of last year
order by LineStatus desc, DueDate asc"""

def apply_filters(dataframe):
    """
    Filter by open status (i.e. remove closed orders)
    """
    def is_open(df):
        return df["LineStatus"] == "O"
    return dataframe[is_open(dataframe)]

@cached(cache=RECENT_ORDERS_CACHE,condition=Condition(Lock()))
def read_recent_orders() -> pd.DataFrame:
    """
    Get the complete recent orders table from the database.
    """
    logger.info("Generating orders table...")
    orders_data = pd.read_sql(ALL_ORDERS_QUERY, sap_database_engine)
    logger.debug(f"Orders table shape:{orders_data.shape}")
    return orders_data

def get_recent_orders(open_only: bool) -> pd.DataFrame:
    """
    
    """
    orders_data = read_recent_orders()
    if open_only:
        logger.info("Filtering orders table by open status...")
        orders_data = apply_filters(orders_data)
    logger.debug(f"Orders table shape:{orders_data.shape}")
    return orders_data