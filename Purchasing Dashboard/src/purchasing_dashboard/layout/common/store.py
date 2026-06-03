from dash import Output, html, dcc
from frozendict import frozendict
from purchasing_dashboard.utils.logging import logger

"""
Common dcc.Store data for all pages.
"""
CUSTOMER_BREAKDOWN_STORE_ID = "customer-breakdown-store"
ORDER_HISTORY_DATA_STORE_ID = "order-history-data"
FORECAST_DATA_STORE_ID = "forecast-data"
VENDOR_ITEMS_DATA_STORE_ID = "vendor-items-data"
ALL_ORDERS_DATA_STORE_ID = "all-orders-data"
OPEN_ORDERS_DATA_STORE_ID = "open-orders-data"
ITEM_CODES_STORE_ID = "item-codes"
PRODUCT_IDS_STORE_ID = "product-ids"


STORE_TO_DEPENDENTS = {
    ALL_ORDERS_DATA_STORE_ID: set[str | frozendict](),
    OPEN_ORDERS_DATA_STORE_ID: set[str | frozendict](),
    VENDOR_ITEMS_DATA_STORE_ID: set[str | frozendict](),
    ORDER_HISTORY_DATA_STORE_ID: set[str | frozendict](),
    FORECAST_DATA_STORE_ID: set[str | frozendict](),
    ITEM_CODES_STORE_ID: set[str | frozendict](),
    PRODUCT_IDS_STORE_ID: set[str | frozendict](),
}
"""
This dictionary maps the store IDs to the IDs of loading wrappers of their dependent components.
It is used to determine which components should have loading wrappers activated when the store data changes.
"""

common_store = html.Div([
    dcc.Location("url"),
    dcc.Store(id=CUSTOMER_BREAKDOWN_STORE_ID, storage_type="session"),
    dcc.Store(id=ITEM_CODES_STORE_ID, storage_type="session"),
    dcc.Store(id=ALL_ORDERS_DATA_STORE_ID, storage_type="session"),
    dcc.Store(id=OPEN_ORDERS_DATA_STORE_ID, storage_type="session"),
    dcc.Store(id=VENDOR_ITEMS_DATA_STORE_ID, storage_type="session"),
    dcc.Store(id=ORDER_HISTORY_DATA_STORE_ID, storage_type="session"),
    dcc.Store(id=PRODUCT_IDS_STORE_ID, storage_type="session"),
])

def get_dependent_outputs_for_store(store_id: str | dict) -> set[str | frozendict]:
    """
    Get the set of Output tuples for the `running` attribute of the `@callback` decorator
    based on dependent component IDs for a given store ID.
    """
    if isinstance(store_id, dict):
        store_id = frozendict(store_id)
        display_id = f"<{store_id['aio_id']}.{store_id['component']}>"
    else:
        display_id = store_id
    dependents = STORE_TO_DEPENDENTS.get(store_id, set())
    logger.debug(f"Getting dependent outputs for store {display_id}: {dependents}")
    if dependents == set():
        logger.warning(f"No dependents found for store with ID: {display_id}. Using dummy loading.")
        dependents = ["dummy-loading"] # Fallback for no dependents
    result = []
    for dependent in dependents:
        result.append((Output(dependent, "display"), "show", "auto"))
    return result