"""
Module to read order data from the historical database with caching.
"""

from threading import Condition, Lock
from data_api.database.database_connection import historical_database_engine as db_conn
from data_api.utils.caching import ORDER_HISTORY_CACHE
from data_api.utils.logging import logger


from pandas import DataFrame, read_sql
from cachetools import cached
HISTORICAL_ORDERS_BY_ITEM_QUERY = """
select b.ItemCode, b.ItemName, a.DocDate [OrderDate],d.groupname [AccountType],SUM(a.Quantity) [Units], SUM(a.Linetotal) [Sales]
from FactSales a
inner join DimItem b on b.ItemKey = a.ItemKey
inner join DimPartner c on c.CardKey = a.CardKey
inner join DimPartnerGroup d on d.groupcode = c.GroupCode
where  a.DocDate between DATEADD(yy, DATEDIFF(yy, 0, GETDATE()) - %(years_back)s, 0) and EOMONTH(getdate(),-1) and linetotal > 0
and b.ItmsGrpCod != 123 -- exclude discontinued items
group by b.ItemCode, b.ItemName, a.DocDate,groupname
"""


@cached(cache=ORDER_HISTORY_CACHE, condition=Condition(Lock()))
def read_order_history(years_back=5) -> DataFrame:
    logger.info(
        f"Fetching historical orders data from up to {years_back} year(s) ago...")
    try:
        order_history_dataframe = read_sql(HISTORICAL_ORDERS_BY_ITEM_QUERY, db_conn, params={"years_back": years_back})
        if type(order_history_dataframe) is not DataFrame:
            raise ValueError("Query did not return a DataFrame")
    except Exception as e:
        logger.error(f"Error fetching historical orders data: {e}")
        raise e
    logger.info(f"Obtained {len(order_history_dataframe)} rows of historical order data")
    return order_history_dataframe