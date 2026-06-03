from dash import Input, Output, State, ctx, callback, no_update
import pandas as pd
from purchasing_dashboard.layout.common.dropdown_labels import generate_option_label
from purchasing_dashboard.layout.common.store import OPEN_ORDERS_DATA_STORE_ID, VENDOR_ITEMS_DATA_STORE_ID

from purchasing_dashboard.utils.logging import logger

@callback(
    Output("vendor-items-purchased-table", "data", allow_duplicate=True),
    Output("open-orders-with-vendor-table", "data", allow_duplicate=True),
    Input("vendor-id-filter", "value"),
    Input("vendor-snapshot-table-search", "value"),
    State(VENDOR_ITEMS_DATA_STORE_ID, "data"),
    State(OPEN_ORDERS_DATA_STORE_ID, "data"),
    Input("vendor-items-purchased-table-loaded", "data"),
    prevent_initial_call=True
)
def filter_table(vendor_ids: list[str], search_term: str, vendor_data: dict, open_orders_data: dict, hasLoaded: bool):
    if(not hasLoaded or not vendor_data or not open_orders_data):
        logger.debug("Can't filter when data hasn't been loaded.")
        return no_update
    vendor_filtered = pd.DataFrame(vendor_data, copy=False)
    oo_filtered = pd.DataFrame(open_orders_data, copy=False)
    vendor_ids = vendor_ids or []
    num_vendor_rows = len(vendor_filtered)
    num_oo_rows = len(oo_filtered)
    if(vendor_ids == []):
        logger.debug("Filter selection is empty.")
    else:
        vendor_filtered = filter_dataframe_by_dropdowns(vendor_ids, vendor_filtered, "VendorCode", num_vendor_rows)
        oo_filtered = filter_dataframe_by_dropdowns(vendor_ids, oo_filtered, "VendorCode", num_oo_rows)
    search_term = search_term or ""
    if(search_term is None or search_term == ""):
        logger.debug("Search term is empty.")
    else:
        vendor_filtered = filter_dataframe_by_search_term(search_term, vendor_filtered, num_vendor_rows)
        oo_filtered = filter_dataframe_by_search_term(search_term, oo_filtered, len(oo_filtered))
    return vendor_filtered.to_dict(orient='records'), oo_filtered.to_dict(orient='records')

def filter_dataframe_by_dropdowns(selected_ids: list[str], dataframe: pd.DataFrame, id_column_name:str, num_rows: int):
    logger.debug(f"Filtering tables according to dropdowns... ids: {selected_ids}")
    selected_id_matches = pd.Series([True] * num_rows) if (selected_ids == []) else dataframe[id_column_name].isin(selected_ids)
    dataframe_filtered = dataframe[selected_id_matches]
    return dataframe_filtered

def filter_dataframe_by_search_term(search_term: str, dataframe: pd.DataFrame, num_rows: int) -> pd.DataFrame:
    logger.debug(f"Filtering table according to search term... search term: {search_term}")
    if (search_term is None or search_term == ""):
        search_term_matches = pd.Series([True] * num_rows) 
    else:
        search_term_matches = pd.Series([False] * num_rows)
        for col in dataframe.columns:
            search_term_matches = search_term_matches | dataframe[col].astype(str).str.contains(search_term, case=False, regex=False)
    dataframe_filtered = dataframe[search_term_matches]
    return dataframe_filtered

@callback(
    Output("vendor-id-filter", "options"),
    Input("vendor-items-purchased-table-loaded", "data"),
    Input(VENDOR_ITEMS_DATA_STORE_ID, "data"),
    Input(OPEN_ORDERS_DATA_STORE_ID, "data"),
    prevent_initial_call=True
)
def populate_vendor_filter_dropdowns(hasLoaded: bool, vendor_data: dict, open_orders_data: dict):
    if(not hasLoaded or not vendor_data or not open_orders_data):
        logger.debug("Table data not loaded yet; can't populate dropdowns")
        return no_update, no_update
    logger.debug("Populating vendor code dropdowns.")
    vendor_codes_and_names = pd.concat(
        [pd.DataFrame(vendor_data), 
         pd.DataFrame(open_orders_data)], 
         ignore_index=True) \
        [["VendorCode", "VendorName"]] \
        .drop_duplicates("VendorCode") \
        .reset_index(drop=True)
    vendor_codes_and_names.sort_values(by="VendorName", inplace=True)

    options = []
    for row in vendor_codes_and_names.itertuples(index=True):
        if row.VendorCode is None or row.VendorCode == "":
            logger.warning(f"Found empty vendor code at index {row.Index}. This will be skipped in the dropdown options.")
            continue
        else:
            option = generate_option_label(
                row.VendorCode, 
                row.VendorName, 
                missing_full_name_placeholder="vendor name"
                )
            options.append(option)

    logger.debug(f"Generated {len(options)} dropdown options.")
    return options

@callback(
    Output("vendor-items-purchased-table", "data"),
    Output("loading-vendor-items-purchased-table", "display"),
    Output("vendor-items-purchased-table-loaded", "data"),
    Input(VENDOR_ITEMS_DATA_STORE_ID, "data"),
    State("vendor-items-purchased-table-loaded", "data"),
)
def fill_vendor_items_purchased_table(cached_data: dict, hasLoaded: bool):
    trigger = ctx.triggered_id

    if hasLoaded:
        logger.debug("Vendor items purchased table has already been loaded into session memory.")
        return no_update, "hide", True
        
    table: pd.DataFrame = pd.DataFrame(cached_data)

    return table.to_dict(orient='records'), "hide", True

@callback(
    Output("open-orders-with-vendor-table", "data"),
    Output("loading-open-orders-table", "display"),
    Output("open-orders-with-vendor-table-loaded", "data"),
    Input(OPEN_ORDERS_DATA_STORE_ID, "data"),
    State("open-orders-with-vendor-table-loaded", "data")
)
def fill_open_orders_table(cached_data: dict, hasLoaded: bool):
    trigger = ctx.triggered_id

    if hasLoaded:
        logger.debug("Open orders table has already been loaded into session memory.")
        return no_update, "hide", True
        
    table = pd.DataFrame(cached_data)
    return table.to_dict('records'), "hide", True