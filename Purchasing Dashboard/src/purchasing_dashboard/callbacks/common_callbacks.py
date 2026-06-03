"""
Callbacks for loading data into the common data stores used across the application.
"""

from datetime import datetime
import io
import time
from dash import Input, Output, State, ctx, callback, no_update
import pandas as pd
from purchasing_dashboard.layout.aio.item_code_selector import ItemCodeSelectorAIO
from purchasing_dashboard.layout.common.store import ALL_ORDERS_DATA_STORE_ID, ITEM_CODES_STORE_ID, OPEN_ORDERS_DATA_STORE_ID, PRODUCT_IDS_STORE_ID, VENDOR_ITEMS_DATA_STORE_ID, get_dependent_outputs_for_store
from purchasing_dashboard.utils.api import api

from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.utils.logging import log_last_loaded
from purchasing_dashboard.utils.logging import log_stale

# TODO #74: deduplicate code between these callbacks

"""
Loads table data from API on page load or when stale data is detected.
"""
def is_stale(timestamp_ms: int):
    """
    The time is considered stale if it's more than STALENESS_TIME_SECONDS seconds old.
    """
    STALENESS_TIME_SECONDS=1800
    since_last_modified = int((datetime.now() - datetime.fromtimestamp(timestamp_ms/1000)).total_seconds())
    return since_last_modified > STALENESS_TIME_SECONDS

def should_fetch_data(last_updated_ms: int | None, store_id: str):
    """
    Determines if data should be fetched based on the last updated timestamp.
    Returns True if the data is stale or if it has never been loaded.
    """
    if not last_updated_ms or last_updated_ms == -1:
        logger.debug(f"No last update for {store_id}")
        return True
    elif is_stale(last_updated_ms):
        log_stale(store_id, last_updated_ms)
        return True
    else:
        log_last_loaded(store_id, last_updated_ms)
        return False

def format_date_columns(df: pd.DataFrame, *date_columns: str):
    """
    Formats timestamp columns in the given list, saving the original timestamp
    in a new column with "TimestampMs" suffix. 
    """
    for col in date_columns:
        df[col + "TimestampMs"] = df[col]
        df[col] = pd.to_datetime(df[col], unit="ms").dropna().dt.strftime("%Y-%m-%d")
    return df

def read_and_rename(json_dataframe: str, column_rename:dict[str,str]) -> pd.DataFrame:
    """
    Reads json_dataframe as a pd.DataFrame, and renames the columns according
    to column_rename. Then returns the result. 
    """
    data: pd.DataFrame = pd.read_json(io.StringIO(json_dataframe))
    data.rename(columns=column_rename, inplace=True)
    return data

@callback(
    Output(VENDOR_ITEMS_DATA_STORE_ID, "data"),
    State(VENDOR_ITEMS_DATA_STORE_ID, "modified_timestamp"),
    Input("url", "pathname"),
    background=True,
    running=get_dependent_outputs_for_store(VENDOR_ITEMS_DATA_STORE_ID),
    prevent_initial_call=True
)
def load_vendor_items_purchased_table(last_updated_ms: int, pathname: str):
    trigger = ctx.triggered_id

    VENDOR_ITEMS_PURCHASED_RENAME = {"CardCode":"VendorCode","CardName":"VendorName","Working_Days_OnHand":"WorkingDaysOnHand"}

    DATA_TABLE_NAME=VENDOR_ITEMS_DATA_STORE_ID

    if not should_fetch_data(last_updated_ms, DATA_TABLE_NAME):
        return no_update
        
    data_json: str = str(api.fetch_inventory_data())
    data: pd.DataFrame = read_and_rename(data_json, VENDOR_ITEMS_PURCHASED_RENAME)

    return data.to_dict(orient='list')

ORDERS_RENAME = {"PO_Num":"PONumber", "CardName": "VendorName"}

@callback(
    Output(OPEN_ORDERS_DATA_STORE_ID, "data"),
    State(OPEN_ORDERS_DATA_STORE_ID, "modified_timestamp"),
    Input("url", "pathname"),
    background=True,
    running=get_dependent_outputs_for_store(OPEN_ORDERS_DATA_STORE_ID),
    prevent_initial_call=True
)
def load_open_orders_table(last_updated_ms: int, pathname: str):
    trigger = ctx.triggered_id

    if not should_fetch_data(last_updated_ms, OPEN_ORDERS_DATA_STORE_ID):
        return no_update
        
    data_json: str = str(api.fetch_open_orders_data())
    data: pd.DataFrame = read_and_rename(data_json, ORDERS_RENAME)
    #special: convert from milliseconds to yy-mm-dd
    data = format_date_columns(data, "DueDate", "OrderDate", "DeliveryDate").to_dict(orient='list')
    return data

@callback(
    Output(ALL_ORDERS_DATA_STORE_ID, "data"),
    State(ALL_ORDERS_DATA_STORE_ID, "modified_timestamp"),
    Input("url", "pathname"),
    prevent_initial_call=True,
    background=True
)
def load_all_orders_table(last_updated_ms: int, pathname: str):

    trigger = ctx.triggered_id
    ALL_ORDERS_DATA_STORE_ID

    if not should_fetch_data(last_updated_ms, ALL_ORDERS_DATA_STORE_ID):
        return no_update
        
    data_json: str = str(api.fetch_open_orders_data(False))
    data: pd.DataFrame = read_and_rename(data_json, ORDERS_RENAME)
    #special: convert from milliseconds to yy-mm-dd
    data = format_date_columns(data, "DueDate", "OrderDate", "DeliveryDate")
    return data.to_dict(orient='list')

@callback(
    Output(ITEM_CODES_STORE_ID, "data"),
    State(ITEM_CODES_STORE_ID, "modified_timestamp"),
    Input("url", "pathname"),
    background=True,
    running=get_dependent_outputs_for_store(ITEM_CODES_STORE_ID),
    prevent_initial_call=True
)
def load_item_ids(last_updated_ms: int, pathname: str):
    trigger = ctx.triggered_id
    if not should_fetch_data(last_updated_ms, ITEM_CODES_STORE_ID):
        return no_update
    try:
        logger.info("Fetching item IDs from API.")
        item_ids = api.fetch_item_ids()
        logger.info(f"Fetched {len(item_ids)} item IDs from API.")
    except Exception as e:
        logger.error(f"Error fetching item IDs: {e}")
        item_ids = no_update
    finally:
        return item_ids
    
    
@callback(
    Output(PRODUCT_IDS_STORE_ID, "data"),
    State(PRODUCT_IDS_STORE_ID, "modified_timestamp"),
    Input("url", "pathname"),
    background=True,
    running=get_dependent_outputs_for_store(PRODUCT_IDS_STORE_ID),
    prevent_initial_call=True
)
def update_product_dropdown(last_updated_ms: int, pathname: str):
    trigger = ctx.triggered_id
    if not should_fetch_data(last_updated_ms, PRODUCT_IDS_STORE_ID):
        return no_update
    try:
        logger.info("Fetching product IDs from API.")
        product_ids = api.fetch_product_ids()
        # logger.debug("Stalling for 2 seconds to simulate slow API...")
        # time.sleep(6)  # Simulate slow API for demo purposes
        logger.info(f"Fetched {len(product_ids)} product IDs from API.")
    except Exception as e:
        logger.error(f"Error fetching product IDs: {e}")
        product_ids = no_update
    finally:
        return product_ids