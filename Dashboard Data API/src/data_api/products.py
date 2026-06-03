from threading import Condition, Lock
from cachetools import cached
from dashboard_common.model.product import Product
import pandas

from data_api.utils.logging import logger
from data_api.utils.caching import PRODUCT_IDS_CACHE, PRODUCTS_CACHE
from data_api.utils.environment_variables import PRODUCTS_CUSTOM_CONDITION, SAP_DATABASE_URL

# Using the B2C, B2B, and B2Rep flags to filter Each-type products
# TODO #41: filter those that wouldn't have any built-out items
PRODUCTS_QUERY = f"""
SELECT DISTINCT
    P.ItemCode        AS ProductCode,
    P.ItemName        AS ProductName
FROM OITM P
WHERE {PRODUCTS_CUSTOM_CONDITION}
ORDER BY P.ItemCode
"""

BUILT_OUT_ITEMS_QUERY = """
SELECT DISTINCT
    P.ItemName,
    P.ItemCode,
    C.ItemCode AS ComponentItemCode
FROM OITM P
LEFT JOIN ITT1 D ON P.ItemCode = D.Father
LEFT JOIN OITM C ON D.Code = C.ItemCode
WHERE P.ItemName NOT LIKE '%labor%'
  AND P.ItmsGrpCod != 123
  AND C.ItmsGrpCod != 123
  AND P.ItemCode IN (
      SELECT L.ItemCode
      FROM RDR1 L
      INNER JOIN ORDR O ON L.DocEntry = O.DocEntry
      WHERE O.DocDate >= DATEADD(YEAR, -%(years_back)s, CAST(GETDATE() AS date))
  )
ORDER BY P.ItemName;
"""

_PATTERN = r"([0-9]+)/CS"


@cached(cache=PRODUCTS_CACHE, condition=Condition(Lock()))
def read_built_out_items(years_back: int = 5) -> pandas.DataFrame:
    params = {'years_back': years_back}
    return pandas.read_sql(BUILT_OUT_ITEMS_QUERY, con=SAP_DATABASE_URL, params=params)

@cached(cache=PRODUCT_IDS_CACHE, condition=Condition(Lock()))
def read_products() -> pandas.DataFrame:
    return pandas.read_sql(PRODUCTS_QUERY, con=SAP_DATABASE_URL)

def get_known_product_ids() -> pandas.DataFrame:
    """
    Retrieve a list of all known product IDs from the database.
    """
    # TODO #41: filter out discontinued or inactive products if needed
    products = read_products()
    # filter out products that do not have at least 2 built-out items
    filtered_products = products.copy()
    for product in products.itertuples():
        built_out = get_built_out_items(product.ProductCode)
        if len(built_out) < 2:
            filtered_products = filtered_products[filtered_products["ProductCode"] != product.ProductCode]
    logger.info(f"Filtered out {len(products) - len(filtered_products)} of {len(products)} products without any built-out items.")
    return filtered_products


def get_built_out_items(parent_item_code: str, years_back: int = 5):
    """
    Retrieve a list of built-out items based on the provided parent item code and years back.

    Also includes the parent item.
    """
    built_out_items_df = read_built_out_items(years_back)
    built_out_items_df = built_out_items_df[(built_out_items_df['ItemCode'] == parent_item_code) | (built_out_items_df['ComponentItemCode'] == parent_item_code)]
    built_out_items_df = built_out_items_df.drop_duplicates(subset=["ItemCode"])
    built_out_items_df["EachesPerCase"] = built_out_items_df["ItemName"].str.extract(_PATTERN, expand=False) \
        .fillna("1") \
        .astype(int)
    json_built_out_items = built_out_items_df.to_dict(orient="records")
    return json_built_out_items
