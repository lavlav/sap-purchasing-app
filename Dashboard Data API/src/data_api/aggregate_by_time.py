from cachetools.keys import hashkey
import pandas as pd
from dashboard_common.model.time_bucket import TimeBucket

def hash_time_bucket_and_item_3(time_bucket: str, item_id: tuple[str], df: pd.DataFrame):
    return hashkey(time_bucket, item_id)


def hash_time_bucket_and_item_4(time_bucket: str, item_id: tuple[str], df: pd.DataFrame, drop_empty: bool):
    return hashkey(time_bucket, item_id, drop_empty)

def aggregate_item_order_history_by_time(time_bucket: str, item_ids: tuple[str], df: pd.DataFrame, drop_empty: bool = False) -> pd.DataFrame:
    df = df.copy()
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], unit="ms")
    df.sort_values(by="OrderDate", inplace=True)
    df = aggregate_by_time(df, TimeBucket[time_bucket], drop_empty)
    return df


def aggregate_by_time(df: pd.DataFrame, bucket: TimeBucket, drop_empty: bool, units_col = "Units",
    date_col = "OrderDate") -> pd.DataFrame:
    """
    Aggregate units by specified time bucket. This operation always returns a copy of
    the original DataFrame.

    Parameters:
        df (pd.DataFrame): Input dataframe with a date column and a units column.
        time_bucket (str): One of 'day', 'week', 'month', 'quarter', 'year'.
        drop_empty (bool): Whether or not to drop periods with 0 units in that timeframe.

    Returns:
        pd.DataFrame: Aggregated dataframe with datetime index and summed units.
    """

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    df.set_index(date_col, inplace=True)
    result = df[units_col].resample(bucket.get_resample_rule()).sum().reset_index()
    # drop points with 0 units
    if drop_empty:
        result = result.loc[result[units_col] != 0]
    return result