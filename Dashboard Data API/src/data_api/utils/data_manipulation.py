import datetime
import pandas as pd
from polars import date
from sklearn.model_selection import train_test_split
from data_api.get_historical_orders_for_item import get_recent_orders as get_all_orders_dataframe
from dashboard_common.model.time_bucket import TimeBucket
import pytimetk
from data_api.utils.logging import logger



def augment_time_series_with_date_derived_features(df: pd.DataFrame, col_name: str = "index", include_non_numeric=True) -> pd.DataFrame:
    """
    Augments the DataFrame with time series features.
    """
    df = pytimetk.augment_timeseries_signature(
        df, date_column=col_name, reduce_memory=True)
    if not include_non_numeric:
        df = df.select_dtypes(include=['number', 'datetime'])

    return df


def generate_forecast_input(last_row, n_forecasts, period, augment=True, include_non_numeric=True):
    """
    Generates future data points starting from the last row of the DataFrame.
    """
    # Generate n_forecasts future data points
    # We'll increment the last date by the period (day/week/month/etc) n_forecasts times
    last_date = pd.to_datetime(last_row['OrderDate'], unit='s')
    last_date = TimeBucket[period].get_start(last_date)
    logger.debug(f"Last date {last_date}")
    dataframe = pd.DataFrame(columns=["OrderDate"])
    # TODO #74 can I use pd.date_range?
    for i in range(1, n_forecasts + 1):
        if period == 'day':
            next_date = last_date + pd.Timedelta(days=i)
        elif period == 'week':
            next_date = last_date + pd.Timedelta(weeks=i)
        elif period == 'month':
            next_date = last_date + pd.DateOffset(months=i)
        elif period == 'quarter':
            next_date = last_date + pd.DateOffset(months=3*i)
        elif period == 'year':
            next_date = last_date + pd.DateOffset(years=i)
        else:
            raise ValueError(f"Unknown period: {period}")
        # Build a new row with the same structure as X
        dataframe.loc[i, 'OrderDate'] = int(next_date.timestamp())
    dataframe['OrderDate'] = pd.to_datetime(dataframe["OrderDate"], unit="s")
    if augment:
        dataframe = set_order_date_as_index(dataframe)
        df = augment_time_series_with_date_derived_features(
            dataframe,
            col_name="OrderDate",
            include_non_numeric=include_non_numeric
        )
    else:
        df = dataframe.copy()
    df['OrderDate'] = df['OrderDate'].astype(
        "int64") // 10**9  # Convert to Unix timestamp
    return df


def augment_time_series_with_resampled_y(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """ 
    Adds features to the DataFrame that are derived from resampling to the specified period.
    """
    # Resample the data for the given period
    periods = [period] if not period == "all" else list(
        bucket.value for bucket in TimeBucket)
    for time_bucket in periods:
        df = df.resample(
            TimeBucket[time_bucket].get_resample_rule(),
            on="OrderDate",
        ).sum(numeric_only=True).reset_index()
    return df


def set_order_date_as_index(df):
    logger.debug("Columns before setting index: " + str(df.columns))
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], unit="s")
    df.dropna(subset=["OrderDate"], inplace=True)
    df.set_index("OrderDate", inplace=True, drop=False)
    # Remove duplicates after setting the index to 'OrderDate'
    if df.index.has_duplicates:
        df = df.sort_index()
        # Group by the index and add a small offset to each duplicate

        def break_ties(group):
            # If only one row, return as is
            if len(group) == 1:
                return group
            # Add microseconds to break ties
            group.index = [idx + pd.Timedelta(microseconds=i)
                           for i, idx in enumerate(group.index)]
            return group
        df = df.groupby(df.index).apply(break_ties)
        # Remove the extra groupby level if present
        if isinstance(df.index, pd.MultiIndex):
            df.index = df.index.droplevel(0)
    return df


def prepare_data_points(
        item_ids: tuple[str],
        period,
        resample=True,
        augment_time_series=True,
        as_dataframe=False,
):
    """
    Prepares the data points for training by a predictor model.
    Args:
        item_ids (str): The item IDs to prepare data for.
        period (str): The time period for the data.
        resample (bool): Whether to resample the data.
        augment_time_series (bool): Whether to augment the time series with additional features.
        include_non_numeric (bool): Whether to include non-numeric columns in the features.
        drop_columns (list): List of columns to drop from the DataFrame.
        as_dataframe (bool): Whether to return the full DataFrame instead of features and target
    """
    df = get_all_orders_dataframe(item_ids)
    if len(df) == 0:
        raise Exception(f"No data for item {item_ids}")
    # Need to copy to prevent issues with modifying a view of the cached DataFrame
    df = df.copy()
    # Drop unimportant columns
    df = set_order_date_as_index(df)
    if resample:
        df = augment_time_series_with_resampled_y(df, period)
    if augment_time_series:
        df = augment_time_series_with_date_derived_features(
            df,
            col_name="OrderDate"
        )
    df.reset_index(inplace=True, drop=True)
    df["OrderDate"] = df["OrderDate"].astype(
        "int64") // 10**9  # Convert to Unix timestamp
    X = df[[col for col in df.columns if df.dtypes[col] !=
            "object" and col not in ["Units", f"Units_{period}", "Sales"]]]
    y = df["Units"]
    if as_dataframe:
        return df
    return X, y


def prepare_training_test_split(item_id, period, X, y):
    if X.empty:
        raise Exception(f"No data for item {item_id} in period {period}")
    
    if len(X) < 3:
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.1, shuffle=False)

    return X_train, X_test, y_train, y_test
