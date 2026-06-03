
from datetime import datetime
from cachetools import cached
import numpy
from pytz import utc
from data_api.aggregate_by_time import aggregate_item_order_history_by_time
from dashboard_common.model.time_bucket import TimeBucket
import pandas as pd
from data_api.database.item_names import read_item_codes_and_names
from dashboard_common.model.customer_distribution import CustomerDistribution

from data_api.database.order_history import read_order_history
from data_api.utils.type_aliases import ItemId

from data_api.utils.logging import logger

class ItemMissingError(Exception):
    def __init__(self, item_ids: set[ItemId]):
        self.missing_item_ids = item_ids

    def __str__(self):
        return f"Items {self.missing_item_ids} not found in the order history."

def get_recent_orders(item_id: str | tuple[str], years_back=5, ignore_missing_items=True) -> pd.DataFrame:
    """
    Get recent orders for a specific item or items within the last `years_back` years.
    If `item_id` is a tuple, it will return orders for all items in the tuple.

    If `ignore_missing_items` is False, it will raise an ItemMissingError if any of the items are not found.
    Otherwise, missing items will not contribute to the result, which means that the returned DataFrame may 
    be empty.
    """
    # TODO #74: raise ItemMissingError in all cases, remove the ignore_missing_items parameter, and handle the error appropriately in the frontend.
    orders_by_item = read_order_history(years_back)
    if isinstance(item_id, str):
        orders_by_item = orders_by_item[orders_by_item["ItemCode"] == item_id]
    elif isinstance(item_id, tuple):
        orders_by_item = orders_by_item[orders_by_item["ItemCode"].isin(
            item_id)]
    n_found_items = orders_by_item["ItemCode"].unique().size
    n_expected_items = len(item_id) if not isinstance(item_id, str) else 1
    if n_found_items != n_expected_items and not ignore_missing_items:
        raise ItemMissingError(
            set(item_id) - set(orders_by_item["ItemCode"].unique()))
    logger.debug(f"Filtered orders for {item_id} : {len(orders_by_item)}")
    return orders_by_item

def get_recent_item_ids(years_back=5) -> pd.DataFrame:
    """
    Get a list of item codes that have been ordered in the last `years_back` years.
    """
    item_ids = read_item_codes_and_names(years_back)
    logger.debug(f"Found {len(item_ids)} unique item codes in the last {years_back} years.")
    return item_ids

def post_recent_orders(item_ids: tuple[str], time_bucket: str = None, years_back=5) -> dict:
    """
    Get recent orders for a specific item or items within the last `years_back` years,
    aggregated by the specified `time_bucket`.

    If no `time_bucket` is provided, the resulting dict will contain entries for all time buckets.
    """
    df = get_recent_orders(item_ids, years_back)
    if df.empty:
        logger.warning(f"No recent orders found for items: {item_ids}")
        return {"data": {}, "calculated_at": pd.Timestamp.now().as_unit("ms").timestamp()}
    result_data = {}
    time_buckets = [time_bucket] if time_bucket else [
        bucket.value for bucket in TimeBucket]
    for bucket in time_buckets:
        df_aggregated = aggregate_item_order_history_by_time(
            bucket, item_ids, df, drop_empty=False)
        result_data[bucket] = df_aggregated.to_dict(orient="records")
    result = {
        "data": result_data,
        "calculated_at": pd.Timestamp.now().as_unit("ms").timestamp()
    }
    return result


def get_customer_distribution_for_items(item_ids: tuple[str], until = None, average_by: TimeBucket = None, years_back=5) -> CustomerDistribution:
    """
    Get a breakdown of customers who have ordered a specific item in the last `years_back` years.

    If `until` is provided, the breakdown will filter orders up to that date.

    If `average_by` is also provided, the breakdown will be averaged over the specified time bucket.
    """
    orders = get_recent_orders(item_ids, years_back, ignore_missing_items=True)
    
    if orders.empty:
        logger.warning(f"No orders found for items: {item_ids}")
        customer_distribution = pd.DataFrame(
            columns=["AccountType", "Units", "Sales"])
    else:
        if until is not None:
            until = utc.localize(until) if until.tzinfo is None else until
            if until > utc.localize(datetime.now()):
                raise ValueError("Attribute until cannot be in the future.")
            until = average_by.get_start(until) if average_by else until # Convert to start of the time bucket if provided
            until = numpy.datetime64(until)
            logger.info(f"Filtering orders until {until}")
            orders = orders[orders["OrderDate"] > until]
        logger.info(f"Calculating customer breakdown for items: {item_ids}")
        # Sort values here, though they will be sorted again in the frontend
        if average_by:
            customer_distribution = orders.groupby(["AccountType", pd.Grouper(key="OrderDate", freq=average_by.get_resample_rule())]).agg(
                Units=("Units", "sum"),
                Sales=("Sales", "sum")
            ).groupby("AccountType").mean(numeric_only=True) \
            .sort_values(by="Units", ascending=False) \
            .reset_index()
            logger.debug(f"Customer distribution with time bucket {average_by}:\n {customer_distribution}")
        else:
            customer_distribution = orders.groupby("AccountType").agg(
                Units=("Units", "sum"),
                Sales=("Sales", "sum")
            ) \
            .sort_values(by="Units", ascending=False) \
            .reset_index()
        n_periods = 1
        customer_distribution.dropna(inplace=True)
        customer_distribution = customer_distribution[customer_distribution["Units"] > 0] # Filter out zero units
        customer_distribution["Units"] = (customer_distribution["Units"] / n_periods).round().astype(int)
        customer_distribution["Sales"] = (customer_distribution["Sales"] / n_periods).round(3)
    # customer_distribution["ItemCode"] = item_id
    return CustomerDistribution(
        item_ids=list(item_ids),
        customer_data=customer_distribution,
        total_units=customer_distribution["Units"].sum(),
        total_sales=customer_distribution["Sales"].sum(),
        calculated_at=pd.Timestamp.now().as_unit("ms").timestamp()
    )
