from datetime import datetime
from dash import Input, Output, State, callback, no_update
import pandas as pd
from purchasing_dashboard.layout.aio.groupable_projection_panel import GroupableProjectionPanelAIO
from purchasing_dashboard.layout.common.store import OPEN_ORDERS_DATA_STORE_ID, VENDOR_ITEMS_DATA_STORE_ID, get_dependent_outputs_for_store
from dashboard_common.model.time_bucket import TimeBucket

from purchasing_dashboard.utils.dataframe import aggregate_by_time

from purchasing_dashboard.utils.logging import logger

@callback(
    Output(GroupableProjectionPanelAIO.ids.store(
        "projected-coverage"), "data"),
    State(GroupableProjectionPanelAIO.ids.store(
        "projected-coverage"), "data"),
    Input("time-interval-picker", "value"),
    Input("item-code-filter", "value"),
    Input(VENDOR_ITEMS_DATA_STORE_ID, "data"),
    Input(OPEN_ORDERS_DATA_STORE_ID, "data"),
    Input("url", "pathname"),
    background=True,
    running=get_dependent_outputs_for_store(GroupableProjectionPanelAIO.ids.store("projected-coverage"))
)
def calculate_projected_coverage(orig_data, time_bucket: str, item_ids: list[str], vendor_data, recent_orders_data, pathname: str):
    """
    Calculates projected coverage for the given item codes and time bucket, based on
    the vendor items data and recent orders data.

    Maybe this should be calculated in the backend instead?
    """
    # Validate args
    if not vendor_data:
        logger.error(
            f"Can't populate projected coverage because vendor data is not loaded.")
        return no_update
    elif not recent_orders_data:
        logger.error(
            f"Can't populate projected coverage because orders data is not loaded.")
        return no_update
    elif item_ids is None or len(item_ids) == 0:
        logger.debug(f"No ItemCode to show projected coverage for.")
        return no_update
    elif pathname != "/byItem":
        logger.debug(f"Not on projected coverage page, skipping calculation.")
        return no_update
    logger.info(
        f"Calculating projected coverage for {item_ids} with {time_bucket} buckets...")

    # Calculate the number of results needed
    num_items = len(item_ids)
    periods = 20
    periods_plus_padding = periods + 1
    max_results = periods * num_items  # 20 bars per item

    # pad by num_items to ensure we can start from the initial in-stock amount
    num_rows_plus_padding = max_results + num_items

    # Get initial in-stock amount and consumption rate
    item_ids.sort()
    vendor_df = pd.DataFrame(vendor_data).dropna(subset=["ItemCode"])
    vendor_df = vendor_df[vendor_df["ItemCode"].isin(item_ids)].drop_duplicates(
        "ItemCode").sort_values(by="ItemCode")
    vendor_df.reset_index(drop=True, inplace=True)
    min_level, in_stock, daily_usage = get_item_statistics(vendor_df, item_ids)
    days_to_depletion = (in_stock - min_level) / \
        daily_usage if (daily_usage > 0).all() else "Infinity"
    logger.debug(
        f"Daily usage:\n {daily_usage}/day" + f"\nIn stock:\n {in_stock}" +
        f"\nEstimate {days_to_depletion} days to depletion")

    # Get the start of the period
    today = datetime.today()
    current_period_start = TimeBucket(time_bucket).get_start(today)
    coverage_df = pd.DataFrame(
        columns=["Item Code", "Time", "Usage", "Incoming", "Units Available"])

    # Generate the dates to project
    time_series = pd.date_range(
        current_period_start,
        freq=TimeBucket(time_bucket).get_resample_rule(),
        periods=periods_plus_padding) \
        .repeat(num_items)
    coverage_df["Time"] = pd.Series(time_series)
    coverage_df["Item Code"] = pd.Series(item_ids*num_rows_plus_padding)
    coverage_df["Usage"] = pd.Series(daily_usage*num_rows_plus_padding)
    coverage_df.loc[0:num_items, "Units Available"] = in_stock
    oo_df = pd.DataFrame(recent_orders_data)
    oo_df["DueDate"] = pd.to_datetime(oo_df["DueDate"], format="%Y-%m-%d")
    # hack: Add 0-quantity fake orders to the end to ensure we have the right number of rows
    # after aggregating
    empty_quantities = pd.Series([0] * num_rows_plus_padding)
    fake_orders_item_codes = item_ids * periods_plus_padding
    fake_orders = pd.DataFrame(
        columns=["ItemCode", "DueDate", "QuantityOrdered"],
        data={
            "ItemCode": fake_orders_item_codes,
            "DueDate": time_series,
            "QuantityOrdered": empty_quantities
        }
    )
    oo_df = pd.concat([oo_df, fake_orders], axis=0)
    # Filter out past orders and orders that will be due too far in the future
    projected_end_date = time_series[-1]
    oo_df = oo_df[(oo_df["DueDate"] >= current_period_start)
                  & (oo_df["DueDate"] <= projected_end_date)]
    for item_index in range(num_items - 1, -1, -1):
        item = item_ids[item_index]
        item_agg_order_df = oo_df[oo_df["ItemCode"] == (item)].copy()
        item_agg_order_df = aggregate_by_time(item_agg_order_df, time_bucket, drop_empty=False,
                                              units_col="QuantityOrdered", date_col="DueDate")
        item_agg_qty = item_agg_order_df["QuantityOrdered"].fillna(0)
        logger.debug(f"Range: {item_agg_qty.index} for {item}")
        item_agg_qty.index = pd.Index(
            range(item_index, item_index + num_rows_plus_padding, num_items))
        coverage_df.loc[item_agg_qty.index, "Incoming"] = item_agg_qty

        # Calculate in stock values at each time period
        for i in range(item_index, max_results, num_items):
            days_until_next = (
                coverage_df.iloc[i+num_items, 1] - coverage_df.iloc[i, 1]).days
            coverage_df.iloc[i, 2] = days_until_next * daily_usage[item_index]
            # "Usage" - "Incoming"
            in_stock[item_index] = in_stock[item_index] - \
                coverage_df.iloc[i, 2] + coverage_df.iloc[i, 3]
            coverage_df.iloc[i, 4] = in_stock[item_index]
        coverage_df.drop(coverage_df.index.max(), inplace=True)
    # logger.debug(f"Projected coverage for {item_ids}:\n{result_df}")
    coverage_df = coverage_df.round({"Usage": 0, "Units Available": 0})
    coverage_df["Time"] = coverage_df["Time"].dt.strftime("%Y-%m-%d")

    # Aggregate across items
    aggregated_coverage_df = coverage_df.copy().groupby("Time").sum().reset_index()
    aggregated_coverage_df["Item Code"] = "All Items"

    orig_data["individual_dataframe"] = coverage_df.to_dict("list")
    orig_data["grouped_dataframe"] = aggregated_coverage_df.to_dict("list")
    orig_data["dashed_line_threshold"] = min_level.sum()

    # Add clarifying tooltip
    # orig_data["tooltip"] = [f"From the start of the {time_bucket}"]
    # orig_data["tooltip_columns"] = ["Units Available"]
    return orig_data


def get_item_statistics(vendor_df, item_ids):
    """
    Calculate the daily usage, in-stock units, and days on hand for the given item codes.
    """
    num_items = len(item_ids)
    if (len(vendor_df) < num_items):
        missing_items = set(item_ids) - set(vendor_df["ItemCode"].unique())
        logger.warning(
            f"Missing vendor data for items: {missing_items}! Marking them as None.")
        false_data_rows = pd.DataFrame({
            "ItemCode": list(missing_items),
            "DailyRunRate": [None] * len(missing_items),
            "InStock": [None] * len(missing_items),
            "MinInventoryLevel": [None] * len(missing_items)
        })
        vendor_df = pd.concat([vendor_df, false_data_rows], ignore_index=True)
    elif (len(vendor_df) > num_items):
        logger.warning(
            f"Found items {vendor_df['ItemCode']} in vendor data, but only {num_items} were requested!")
    try:
        daily_usage = vendor_df["DailyRunRate"].fillna(0).copy()
    except KeyError:
        logger.error(f"No DailyRunRate for {item_ids}. Assuming 0...")
        daily_usage = pd.Series([0] * num_items)
    try:
        in_stock = vendor_df["InStock"].fillna(0).copy()
    except KeyError:
        logger.error(f"No InStock for {item_ids}. Assuming 0...")
        in_stock = pd.Series([0] * num_items)
    if len(item_ids) == 1:
        try:
            min_level = vendor_df["MinInventoryLevel"]
        except KeyError:
            logger.error(f"No MinLevel for {item_ids}. Assuming 0...")
            min_level = pd.Series([0] * num_items)
    else:
        logger.debug(f"Multiple items selected, using 0 as min level")
        min_level = pd.Series([0] * num_items)

    return min_level, in_stock, daily_usage
