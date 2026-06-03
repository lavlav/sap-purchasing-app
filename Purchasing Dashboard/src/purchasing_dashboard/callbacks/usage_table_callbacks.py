import cachetools
from cachetools.keys import hashkey
from purchasing_dashboard.layout.aio.summary_table import HISTORIC_USAGE_TABLE_COLUMNS, SummaryTableAIO
from purchasing_dashboard.layout.common.inline_styles import STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL
from purchasing_dashboard.layout.common.store import FORECAST_DATA_STORE_ID, ORDER_HISTORY_DATA_STORE_ID
from purchasing_dashboard.utils.info_messages import prompt_to_generate_forecast_message, usage_table_styling_info
from dash import Input, Output, State, callback, html, no_update
from dashboard_common.model.forecast import ForecastSet
from dashboard_common.model.order_aggregation import OrderAggregation
from dashboard_common.model.time_bucket import TimeBucket
from purchasing_dashboard.utils.logging import logger
import pandas as pd


from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.utils.placeholder_data import generate_placeholder_table_data

def pivot_order_dataframe(df: pd.DataFrame, time_bucket: str, time_column: str = "OrderDate") -> pd.DataFrame:
    """
    Pivot the historical dataframe into the format expected by a usage table on the selected time bucket.
    """
    logger.debug(f"Pivoting historical dataframe for time bucket: {time_bucket}")
    logger.debug(f"Shape before pivot: {df.shape}")
    # Multi-index on "Type"
    
    if time_bucket == "month":
        df["Year"] = df[time_column].dt.year
        df["Month"] = df[time_column].dt.month_name().str[:3]
        pivot_df = df.pivot_table(index="Year", columns="Month", values=["Units", "Type"], aggfunc="sum")
        index_col = "Year"
    elif time_bucket == "quarter":
        df["Year"] = df[time_column].dt.year
        df["Quarter"] = "Q" + df[time_column].dt.quarter.astype(str)
        pivot_df = df.pivot_table(index="Year", columns="Quarter", values=["Units", "Type"], aggfunc="sum")
        index_col = "Year"
    elif time_bucket == "year":
        pivot_df = df
        pivot_df["Year"] = df[time_column].dt.year
        index_col = "Year"
    else:
        # For day and week, we can just use the original dataframe
        pivot_df = df
        pivot_df["Date"] = pivot_df[time_column].dt.strftime("%Y-%m-%d")  # Format date for display
        index_col = "Date"
    # Reset index to make it easier to work with
    pivot_df.reset_index(inplace=True)
    pivot_df.set_index(index_col, inplace=True, drop=False)
    types_df = pivot_df.pop("Type")
    if type(pivot_df.columns) is pd.MultiIndex:
        pivot_df.columns = pivot_df.columns.map(lambda x: x[0] if x[0] == index_col else x[1])
    logger.debug(f"Indices: {pivot_df.index} | {types_df.index}")
    logger.debug(f"Columns: {pivot_df.columns}")
    pivot_df.rename(columns={"Units": "UnitsSold"}, inplace=True)  # Rename for clarity
    pivot_df.replace(0, None, inplace=True)  # Replace 0 with None for better display in table
    # logger.debug(f"Pivoted df: {pivot_df}")
    # logger.debug(f"Types df: {types_df}")
    return pivot_df, types_df


def styling_table_info():
    styled_info = html.Span(className="red", children="red")
    message = usage_table_styling_info.copy()
    message.insert(1, styled_info)
    return message

CACHE = cachetools.LRUCache(maxsize=128)

def hash_time_bucket_and_item_4(time_bucket: str, item_id: str, df: dict, df_2: dict):
    return hashkey(time_bucket, item_id)

@cachetools.cached(cache=CACHE, key=hash_time_bucket_and_item_4)
@callback(
    Output(SummaryTableAIO.ids.table("item-demand"), "data"),
    Output(SummaryTableAIO.ids.table("item-demand"), "style_data_conditional"),
    Output(SummaryTableAIO.ids.info_message("item-demand"), "children"),
    Input("time-interval-picker", "value"),
    State("item-code-filter", "value"),
    Input(ORDER_HISTORY_DATA_STORE_ID, "data"),
    Input(FORECAST_DATA_STORE_ID, "data"),
)
def update_historic_usage_table(time_bucket: str, item_ids: list[str], historical_data: dict, forecast_data: dict):
    """
    Update the data of the historic usage table based on the selected time interval.
    """
    if not historical_data:
        return no_update, no_update, no_update  # Will be hidden by the tab content callback
    if not item_ids:
        logger.debug("No item selected. Hiding historic usage table.")
        return no_update, no_update, no_update  # Will be hidden by the tab content callback
    TYPE_FORECAST = 2
    TYPE_HISTORICAL = 1
    # Get the historical data
    historical_dataframe = OrderAggregation.from_dict(historical_data).data[TimeBucket[time_bucket]]
    historical_dataframe["Type"] = TYPE_HISTORICAL
    if historical_dataframe.empty:
        logger.error("No order history data available.")
        return generate_placeholder_table_data(HISTORIC_USAGE_TABLE_COLUMNS), no_update, prompt_to_generate_forecast_message
    logger.debug(
        f"Historic usage data for {item_ids} in {time_bucket} interval: {historical_dataframe.shape[0]} rows.")
    logger.debug(f"Columns: {historical_dataframe.columns.tolist()}")
    # Get the forecast data (if it exists)
    if forecast_data:
        forecast = ForecastSet.from_dict(forecast_data).get(frozenset(item_ids), time_bucket)
    else:
        forecast = None
    conditional_styling_list = STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL
    if forecast is not None:
        logger.debug(f"Forecast data found for {item_ids} in {time_bucket} interval.")
        forecast_dataframe = forecast.forecast_data.round(0)
        forecast_dataframe = forecast_dataframe.rename(columns={"Time": "OrderDate"})
        forecast_dataframe["Type"] = TYPE_FORECAST
        dataframe = pd.concat([historical_dataframe, forecast_dataframe], ignore_index=True)
        message = styling_table_info()
    else:
        logger.debug(f"No forecast data found for {item_ids} in {time_bucket} interval.")
        dataframe = historical_dataframe
        message = prompt_to_generate_forecast_message
    pivot_dataframe, type_dataframe = pivot_order_dataframe(dataframe, time_bucket)
    cells_to_style = type_dataframe[type_dataframe == TYPE_FORECAST]
    if not cells_to_style.empty:
        if type(cells_to_style) is pd.DataFrame:
            cells_to_style = cells_to_style.stack()
            conditional_styling_list += [
                {
                    "if": {
                        "filter_query": f"{{{pivot_dataframe.index.name}}} = '{idx}'",
                        "column_id": col,
                    },
                    "color": "red",
                }
                for idx, col in cells_to_style.index
            ]
        elif type(cells_to_style) is pd.Series: # Series
            conditional_styling_list += [
                {
                    "if": {
                        "filter_query": f"{{{pivot_dataframe.index.name}}} = '{idx}'",
                        "column_id": "UnitsSold",
                    },
                    "color": "red",
                }
                for idx in cells_to_style.index
            ]
    logger.debug(
        f"Pivoted data for {item_ids} in {time_bucket} interval: {pivot_dataframe.shape[0]} rows.")
    logger.debug(f"Columns after pivot: {pivot_dataframe.columns.tolist()}")
    return pivot_dataframe.to_dict("records"), conditional_styling_list, message