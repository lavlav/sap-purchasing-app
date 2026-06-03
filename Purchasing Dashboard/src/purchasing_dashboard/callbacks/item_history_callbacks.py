import functools
from dash import ALL, Input, Output, State, callback, no_update
from purchasing_dashboard.layout.aio.tab_content_container import TabContentContainerAIO
from purchasing_dashboard.layout.common.dropdown_labels import generate_option_label
from purchasing_dashboard.layout.common.store import ALL_ORDERS_DATA_STORE_ID, ITEM_CODES_STORE_ID, ORDER_HISTORY_DATA_STORE_ID, VENDOR_ITEMS_DATA_STORE_ID, get_dependent_outputs_for_store
from purchasing_dashboard.utils.info_messages import units_in_stock_tooltip
from dashboard_common.model.order_aggregation import OrderAggregation
from purchasing_dashboard.utils.api import api
import pandas as pd

from purchasing_dashboard.utils.classnames import toggle_class, toggle_hidden_class

from purchasing_dashboard.utils.logging import logger

def is_container_selected(active_tab: str, container_id: dict):
    corresponding_div_name = f"{active_tab[:-4]}-container"
    return corresponding_div_name == container_id["aio_id"]

@callback(
    Output("time-interval-picker", "options"),
    State("time-interval-picker", "options"),
    State(TabContentContainerAIO.ids.time_dependency_store(ALL), "id"),
    State(TabContentContainerAIO.ids.time_dependency_store(ALL),
          "data"),
    Input("item-code-filter", "value"),
    Input("tabs", "value"),
)
def toggle_options(options: list[dict], store_aio_ids: list, depends: list[dict[str,bool]], item_ids: list[str], active_tab: str):
    """
    Gray out the radio buttons when changing them wouldn't affect the current tab.
    """
    if (item_ids and len(item_ids) > 0 and len(store_aio_ids) > 0):
        # If an item is selected, disable based on if the tab declares it needs it
        disabled = True
        for i in range(len(store_aio_ids)):
            if (is_container_selected(active_tab, store_aio_ids[i])):
                disabled = not depends[i]
    else:
        # Disable when no item selected
        disabled = True
    for option in options:
        option["disabled"] = disabled
    return options

# TODO #12 coalesce into a class with this functionality built-in
@callback(
    Output("most-recent-price-label", "className"),
    State("most-recent-price-label", "className"),
    Input("most-recent-price-label", "title"),
)
@callback(
    Output("avg-monthly-usage-label", "className"),
    State("avg-monthly-usage-label", "className"),
    Input("avg-monthly-usage-label", "title"),
)
@callback(
    Output("days-on-hand-label", "className"),
    State("days-on-hand-label", "className"),
    Input("days-on-hand-label", "title"),
)
@callback(
    Output("units-in-stock-label", "className"),
    State("units-in-stock-label", "className"),
    Input("units-in-stock-label", "title"),
)
def indicate_tooltips(class_name: str, tooltip: str):
    """
    Style labels to indicate that they have tooltips.
    """
    return toggle_class(class_name, "with-tooltip", tooltip is not None)

@callback(
    Output("most-recent-price-label", "children"),
    Output("most-recent-price-label", "title"),
    State("item-code-filter", "value"),
    State(ALL_ORDERS_DATA_STORE_ID, "data"),
    Input(ORDER_HISTORY_DATA_STORE_ID, "data"),    # only used to trigger the callback
)
def calculate_most_recent_price(item_ids: list[str], orders_data: dict, _): #
    """
    Calculate the most recent price per unit for the selected item.
    """
    if (not item_ids):
        return "...", None
    if (len(item_ids) > 1):
        logger.debug("Multiple item IDs selected, cannot calculate most recent price.")
        return "N/A", "Not available for groups of items"
    item_id = item_ids[0]
    if (not orders_data):
        logger.error(
            "Can't update Most Recent Price info box because no order history data.")
        return "N/A", None
    df = pd.DataFrame.from_dict(orders_data)
    df = df[df["ItemCode"] == item_id]
    if (len(df) == 0):
        logger.error(f"No order history data for {item_id}.")
        return "N/A", None
    df.sort_values(by="OrderDate", inplace=True)
    most_recent_price_per_unit = df.at[df.index.min(), "Price"]
    most_recent_units = df.at[df.index.min(), "QuantityOrdered"]
    most_recent_order_date = df.at[df.index.min(), "OrderDate"]
    logger.debug(
        f"Most recent price for {item_id} is {most_recent_price_per_unit} from order on {most_recent_order_date}.")
    if (most_recent_price_per_unit is None):
        logger.error(f"Most recent price for {item_id} is None.")
        return "N/A", None
    if (most_recent_units is None or most_recent_units == 0):
        logger.error(
            f"Most recent units for {item_id} is {most_recent_units}.")
        return "N/A", None
    most_recent_price_total = most_recent_price_per_unit * most_recent_units
    return f"${most_recent_price_per_unit:,.3f}", f"From ${most_recent_price_total:,.2f} order for {most_recent_units} units on {most_recent_order_date}"


@callback(
    Output("item-order-history-table", "data"),
    Output("item-order-history-table", "hidden_columns"),
    Input("item-code-filter", "value"),
    Input(ALL_ORDERS_DATA_STORE_ID, "data"),
)
def fill_item_order_history_table(item_ids: list[str], data: dict): #
    """ 
    Fill the item order history table with data for the selected item.
    """
    if (not data):
        logger.error("No order history data available.")
        return no_update, no_update
    if (not item_ids or len(item_ids) == 0):
        logger.debug("No item selected. Hiding item order history table.")
        return None, no_update
    hidden = ["ItemCode"] if len(item_ids) == 1 else []
    df = pd.DataFrame(data).dropna(subset="ItemCode")
    df = df[df["ItemCode"].isin(item_ids)] \
        .sort_values(by="DeliveryDate", ascending=False)
    return df.to_dict("records"), hidden


@callback(
    Output("no-item-selected-info-div", "className"),
    Output("tabs", "content_className"),
    Input("item-code-filter", "value"),
    State("tabs", "content_className"),
    State("no-item-selected-info-div", "className")
)
def toggle_tab_content_visibility(item_ids, tabs_content_classname, no_item_selected_info_classname): #
    item_id_selected = item_ids is not None and item_ids != []
    return toggle_hidden_class(no_item_selected_info_classname, item_id_selected), \
           toggle_hidden_class(tabs_content_classname, not item_id_selected)


@callback(
    Output("days-on-hand-label", "children"),
    State("item-code-filter", "value"),
    State(VENDOR_ITEMS_DATA_STORE_ID, "data"),
    Input(ORDER_HISTORY_DATA_STORE_ID, "data"),    # only used to trigger the callback
)
def calculate_days_on_hand(item_ids: list[str], vendor_data: dict, _: dict): #
    """
    Calculate the days on hand for the selected item from vendor data.
    """
    if (item_ids is None or len(item_ids) == 0):
        return "..."
    if (len(item_ids) > 1):
        logger.debug("Multiple item IDs selected, cannot calculate days on hand.")
        return "N/A"
    if (not vendor_data):
        logger.error(
            "Can't update Days on Hand info box because no vendor data.")
        return "N/A"
    item_id = item_ids[0]
    df = pd.DataFrame(vendor_data).dropna(subset="WorkingDaysOnHand")
    df = df[df["ItemCode"] == item_id]
    if (len(df) == 0):
        logger.error(f"No WorkingDaysOnHand data for {item_id}.")
        return "N/A"
    days_on_hand = df.at[df.index.min(), "WorkingDaysOnHand"]
    if (days_on_hand <= 0):
        logger.warning(
            f"Days on hand for {item_id} is a negative number ({days_on_hand}).")
    if (days_on_hand > 365 * 5):
        logger.warning(
            f"Days on hand for {item_id} is suspiciously high ({days_on_hand}).")
    if (days_on_hand is None):
        logger.error(f"Days on hand for {item_id} is None.")
        return "N/A"
    return f"{round(days_on_hand):,}"  # Format with commas for readability

@callback(
    Output("avg-monthly-usage-label", "children"),
    Output("avg-monthly-usage-label", "title"),
    State("item-code-filter", "value"),
    Input(ORDER_HISTORY_DATA_STORE_ID, "data")
)
def calculate_average_monthly_usage(item_ids: list[str], order_hist_data: dict):
    """
    Calculate the mean of the units in the last 6 months with orders,
    and return the mean.
    """
    if (not order_hist_data):
        return "...", None
    dataframe: pd.DataFrame = OrderAggregation.from_dict(order_hist_data).data["month"]
    # Average across the last 6 months with orders
    dataframe = dataframe[dataframe["Units"] > 0].tail(6)
    if (len(dataframe) == 0):
        return "0", None
    average = f"{round(dataframe["Units"].mean()):,}"
    tooltip = "Averaged over:"
    for date in dataframe["OrderDate"]:
        tooltip = f"{tooltip}\n-{date.strftime("%b %Y")}"
    return str(average), tooltip


@callback(
    Output("units-in-stock-label", "children"),
    Output("units-in-stock-label", "title"),
    Input("item-code-filter", "value"),
    Input(VENDOR_ITEMS_DATA_STORE_ID, "data"),
)
def calculate_units_in_stock(item_ids: list[str], vendor_data: dict):
    """
    Calculate the total units in stock for the selected items from vendor data.
    """
    if (not item_ids or len(item_ids) == 0):
        return "...", None
    if (not vendor_data):
        logger.error("Can't update InStock info box because no vendor data.")
        return "N/A", None
    df = pd.DataFrame(vendor_data).dropna(subset="InStock")
    df = df[df["ItemCode"].isin(item_ids)]
    if (len(df) < len(item_ids)):
        missing_items = set(item_ids) - set(df["ItemCode"])
        logger.error(f"No InStock summary data for {missing_items}.")
        return "N/A", None
    if (len(df) > len(item_ids)):
        no_dupes = df.drop_duplicates(subset="ItemCode")
        overfull_items = set(df["ItemCode"]) - set(item_ids)
        logger.warning(f"Multiple InStock entries: {overfull_items}. Sum may be incorrect.")
        df = no_dupes
    result = f"{round(df["InStock"].sum()):,}"
    tooltip = units_in_stock_tooltip
    tooltip += "\n".join([f"- {row.ItemCode}: {round(row.InStock):,}" for row in df.itertuples()])
    return result, tooltip

@functools.lru_cache
@callback(
    Output(ORDER_HISTORY_DATA_STORE_ID, "data"),
    Input("item-code-filter", "value"),
    background=True,
    running=get_dependent_outputs_for_store(ORDER_HISTORY_DATA_STORE_ID),
    prevent_initial_call=True
)
def get_order_history_for_selected_item(item_ids: list[str]):
    """
    Fetch order history for the selected item with the API.
    Then parses the api call into a dataframe. Expensive.
    """
    #for dependent in STORE_TO_DEPENDENTS[ORDER_HISTORY_DATA_STORE_ID]:
    #    set_props(next(iter(dependent)), {"display": "show"})
    if (not item_ids or len(item_ids) == 0):
        return None
    time_initiated = pd.Timestamp.now().as_unit("ms").timestamp()
    response = api.fetch_order_history(item_ids)

    order_history_data = response["data"]
    time_computed = response["calculated_at"]
    order_aggregation = OrderAggregation.from_dict({
        "data": order_history_data,
        "item_codes": frozenset(item_ids),
        "time_initiated": time_initiated,
        "time_computed": time_computed
    })
    logger.debug("Fetched order history data for item(s): %s", item_ids)
    return order_aggregation.to_dict()


@callback(
    Output("item-code-filter", "options"),
    Input(ITEM_CODES_STORE_ID, "data"),
)
def populate_item_code_dropdown(data):
    df = pd.DataFrame(data)
    if df.empty:
        return [{
            "label": "\u274c Error: no items found \u274c",
            "value": "error_no_items_found",
            "disabled": True,
        }]
    df.sort_values(by="ItemName", inplace=True)
    options = []
    for row in df.itertuples():
        option = generate_option_label(
            shorthand_code=row.ItemCode,
            full_name=row.ItemName
        )
        options.append(option)
    return options

