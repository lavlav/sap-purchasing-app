"""
Utility functions for generating Planned Independent Requirements (PIR) data
for export to SAP.
"""

from datetime import datetime
from dashboard_common.model.time_bucket import TimeBucket
from dashboard_common.model.forecast import Forecast, ForecastSet
import pandas as pd

# From the template
FIXED_COLUMNS = ["MaterialID", "Plant", "MRPArea", "Version", "ReqType", "VersionActive", "ReqPlan", "ReqSeg", "UoM"]

def append_date_columns(
        start_date: datetime = datetime.today(), 
        num_months: int = 12,
        ) -> list:
    """
    Append num_months date columns to the PIR DataFrame.

    Args:
        start_date (datetime): The starting date for the columns.
        num_months (int): The number of months to append.
    Returns:
        list: List of column names including fixed PIR columns and date columns.
    """
    date_columns = []
    start_date = TimeBucket.month.get_start(start_date)
    for i in range(start_date.month, start_date.month + num_months):
        offset = i - start_date.month
        offset_date = start_date + pd.DateOffset(months=offset)
        date_columns.append(offset_date.strftime("M%m.%Y"))
    return FIXED_COLUMNS + date_columns

def fill_fixed_pir_columns(dataframe):
    """
    See [George's comment](https://github.com/lavlav/OCuSOFT-Purchasing-App/issues/45#issuecomment-3207246605) on #45 for reference.
    """
    dataframe["Plant"] = dataframe["MRPArea"] = "1710"
    dataframe["ReqType"] = "VSF"
    dataframe["VersionActive"] = dataframe["Version"] = "00"
    # ReqPlan is left blank
    # ReqSeg is left blank
    return dataframe

def generate_pir_dataframe(
        item_codes: list[str],
        forecasts: ForecastSet,
        start_date: datetime = datetime.today(),
        num_months: int = 12
) -> pd.DataFrame:
    """
    Generate a `DataFrame` for Planned Independent Requirements (PIR) data.

    Args:
        item_codes (list[str]): List of item codes to include in the PIR.
        forecast (Forecast): Forecast data containing demand information.
        start_date (datetime): The starting date for the PIR columns.
        num_months (int): The number of months to include in the PIR.

    Returns:
        pd.DataFrame: DataFrame containing PIR data with specified columns.
    """
    dataframe = pd.DataFrame(columns=append_date_columns(start_date, num_months))
    for item_code in item_codes:
        forecast: Forecast = forecasts.get(item_code, TimeBucket.month)
        if not forecast:
            raise ValueError(f"No forecast data available for item code: {item_code}")
        if forecast.num_forecasted_points < num_months:
            raise ValueError(f"Forecast data for item code {item_code} does not cover the required number of months: {num_months}")
        forecasted_item_data = forecast.forecast_data
        forecasted_item_data = pivot_forecast_dataframe(forecasted_item_data, item_code)
        dataframe = pd.concat([dataframe, forecasted_item_data], ignore_index=True)
    dataframe = fill_fixed_pir_columns(dataframe)
    return dataframe
    
def pivot_forecast_dataframe(dataframe: pd.DataFrame, item_code: str) -> pd.DataFrame:
    """
    Pivot the forecast DataFrame to have a more suitable format for PIR.

    Args:
        df (pd.DataFrame): DataFrame containing forecast data.

    Returns:
        pd.DataFrame: Pivoted DataFrame with 'Units' as values.
    """
    dataframe["MaterialID"] = item_code
    dataframe["Month"] = dataframe["Time"].dt.strftime("M%m.%Y")
    dataframe = dataframe.pivot(index=["MaterialID"],
                        columns="Month", values="Units").reset_index()
    dataframe.columns.name = None  # Remove the name of the columns index
    return dataframe