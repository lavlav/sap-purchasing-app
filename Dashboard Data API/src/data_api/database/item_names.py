from threading import Condition, Lock
from cachetools import cached
from pandas import DataFrame, read_sql
from data_api.utils.caching import ITEM_CODES_AND_NAMES_CACHE
from data_api.utils.logging import logger
from data_api.database.database_connection import historical_database_engine as db_conn

ITEM_CODES_AND_NAMES_QUERY = """
select distinct b.ItemCode, b.ItemName
from FactSales a
inner join DimItem b on b.ItemKey = a.ItemKey
inner join DimPartner c on c.CardKey = a.CardKey
inner join DimPartnerGroup d on d.groupcode = c.GroupCode
where  a.DocDate between DATEADD(yy, DATEDIFF(yy, 0, GETDATE()) - %(years_back)s, 0) and EOMONTH(getdate(),-1) and linetotal > 0
and b.ItmsGrpCod != 123 -- exclude discontinued items
group by b.ItemCode, b.ItemName, a.DocDate,groupname
"""

@cached(cache=ITEM_CODES_AND_NAMES_CACHE,condition=Condition(Lock()))
def read_item_codes_and_names(years_back=5) -> DataFrame:
    logger.info(
        f"Fetching item codes and names from up to {years_back} year(s) ago...")
    item_codes_and_names_dataframe = read_sql(ITEM_CODES_AND_NAMES_QUERY, db_conn, params={"years_back": years_back})
    logger.info(f"Obtained {len(item_codes_and_names_dataframe)} unique item codes and names")
    return item_codes_and_names_dataframe