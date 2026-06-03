import pandas as pd
from dashboard_common.model.time_bucket import TimeBucket

def aggregate_by_time(df: pd.DataFrame, period: str, drop_empty: bool, units_col = "Units",
    date_col = "OrderDate") -> pd.DataFrame:
    """
    Aggregate units by specified time period. This operation always returns a copy of
    the original DataFrame.

    Parameters:
        df (pd.DataFrame): Input dataframe with a date column and a units column.
        period (str): One of 'day', 'week', 'month', 'quarter', 'year'.
        drop_empty (bool): Whether or not to drop result rows with 0 units in that timeframe.

    Returns:
        pd.DataFrame: Aggregated dataframe with datetime index and summed units.
    """

    if period not in {"day", "week", "month", "quarter", "year"}:
        raise ValueError(
            "period must be one of: 'day', 'week', 'month', 'quarter', 'year'")

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    result = df[units_col].resample(TimeBucket[period].get_resample_rule()).sum().reset_index()
    # drop points with 0 units
    if drop_empty:
        result = result.loc[result[units_col] != 0]
    return result