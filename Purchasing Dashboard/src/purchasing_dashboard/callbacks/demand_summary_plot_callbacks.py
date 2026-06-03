from typing import Any
from statsmodels.nonparametric.smoothers_lowess import lowess
from dash import Input, Output, State, callback, ctx, no_update
import pandas as pd
import plotly.graph_objects as pgo
import logging

from purchasing_dashboard.layout.common.store import FORECAST_DATA_STORE_ID, ORDER_HISTORY_DATA_STORE_ID
from dashboard_common.model.forecast import Forecast, ForecastSet
from dashboard_common.model.order_aggregation import OrderAggregation
from dashboard_common.model.time_bucket import TimeBucket
from purchasing_dashboard.utils.string_manipulation import truncate_string

from purchasing_dashboard.utils.logging import logger


@callback(
    Output("historic-demand-plot", "figure"),
    State("historic-demand-plot", "figure"),
    State("item-code-filter", "value"),
    Input("time-interval-picker", "value"),
    Input(ORDER_HISTORY_DATA_STORE_ID, "data"),
    Input(FORECAST_DATA_STORE_ID, "data"), 
    prevent_initial_call=True,
)
def plot_demand(figure_raw: dict, item_ids: list[str], time_bucket: str, historic_data: dict, forecast_data: dict):
    #
    if (not item_ids or len(item_ids) == 0):
        return no_update
    logger.debug(f"Preparing to plot data for {item_ids}")
    figure = pgo.Figure(figure_raw)
    if (not historic_data):
        logger.debug(f"No historic data loaded yet for {item_ids}")
    if ctx.triggered_id == "time-interval-picker":
        logger.info(
            "Plot triggered by time interval change, removing forecast data from plot.")
    elif ctx.triggered_id == ORDER_HISTORY_DATA_STORE_ID:
        logger.debug("Plot triggered by order history loading.")
    elif ctx.triggered_id == FORECAST_DATA_STORE_ID:
        logger.debug(f"Plot triggered by forecast data loading.")
    else:
        logger.warning("Plot callback triggered by unknown event.")
    # Clear existing traces
    figure.data = []

    order_aggregation = OrderAggregation.from_dict(historic_data)
    historic_dataframe = order_aggregation.data.get(TimeBucket[time_bucket], pd.DataFrame())
    x_data = historic_dataframe["OrderDate"].to_list()
    y_data = historic_dataframe["Units"].to_list()
    hist_dataframe_no_zeroes = historic_dataframe[historic_dataframe["Units"] > 0]
    x_data_no_zeroes = hist_dataframe_no_zeroes["OrderDate"].to_list()
    y_data_no_zeroes = hist_dataframe_no_zeroes["Units"].to_list()
    # Plot historic data
    plot_historic_data(
        figure=figure,
        x_data=x_data_no_zeroes,
        y_data=y_data_no_zeroes,
        trace_meta=f"Orders_{item_ids}_{time_bucket}"
        )

    # Add LOWESS smoothing line
    if (len(x_data_no_zeroes) < 20):
        logger.info(
            f"Not enough data points to smooth {item_ids} in {time_bucket} interval.")
    else:
        logger.info(f"Plotting smoothed curve for {item_ids}")
        plot_smoothed_curve(x_data, y_data, figure)

    # Plot forecast data
    forecast = ForecastSet.from_dict(forecast_data).get(item_ids, time_bucket) if forecast_data else None
    should_plot_forecast_data = forecast is not None
    if should_plot_forecast_data:
        plot_forecast_data(figure, forecast, [x_data[-1], y_data[-1]], f"Forecast_{item_ids}_{time_bucket}")
    else:
        # If no forecast data is available, remove any existing forecast traces
        logger.debug(f"No forecast data available to plot for {item_ids} in {time_bucket} interval.")
        figure.data = [
            trace for trace in figure.data if not is_forecast_trace(trace)]
    # resize y-axis
    figure.update_yaxes(range=[0, max(y_data) * 1.2], showgrid=True, zeroline=True,)
    # Set plot title
    truncated_item_ids = truncate_string(", ".join(item_ids), 50)
    figure.update_layout(
        title_text=f"Orders over time for {truncated_item_ids} ", title_x=0.5)
    return figure

def plot_historic_data(figure: pgo.Figure, x_data, y_data, trace_meta):
    """
    Plots the historic demand data for the specified item IDs and time bucket.
    """
    # Add the orders trace
    figure.add_trace(
        pgo.Scatter(
            x=x_data,
            y=y_data,
            mode="lines+markers",
            name="Orders",
            legendgroup="orders",
            legendgrouptitle=dict(text="Orders"),
            customdata=[trace_meta],
            line=dict(color="black"),
            marker=dict(size=5),
            hovertemplate="<b>Time:</b> %{x}<br><b>Units:</b> %{y}<extra></extra>",
        )
    )


def is_forecast_trace(trace: Any):
    return trace.name == "Forecast"


def plot_forecast_data(
        figure: pgo.Figure, 
        forecast: Forecast, 
        concat_point: list = None, 
        forecast_trace_meta: str = None
        ) -> pgo.Figure:
    """
    Plots the forecast graph for a specific item and time bucket.
    """
    df = forecast.forecast_data
    if df.empty:
        logger.warning("Forecast data is empty, cannot plot.")
        return no_update
    # df.rename(columns={"OrderDate": "Time"}, inplace=True)
    # connect to last point of previous trace
    if concat_point is not None:
        last_x = concat_point[0]
        last_y = concat_point[1]
        logger.debug(
            f"Last point of previous trace: OrderDate(Time)={last_x}, Units={last_y}")
        df = pd.concat([pd.DataFrame({"Time": [last_x], "Units": [
                       last_y], "Prediction": False}), df], ignore_index=True)
    else:
        logger.warning(
            "No previous trace data for order history found to concatenate forecast line to.")
    x_data = df["Time"].to_list()
    y_data = df["Units"].to_list()
    # If we concatenated a previous point, plot the first segment as dotted, rest as solid
    if len(x_data) > 1 and not df.loc[0, "Prediction"]:
        # Dotted segment from last Orders point to first forecast point
        figure.add_trace(
            pgo.Scatter(
                x=x_data[:2],
                y=y_data[:2],
                mode="lines",
                name="Forecast",
                legendgroup="Forecast",
                showlegend=False,
                customdata=[forecast_trace_meta],
                line=dict(color="red", dash="dot"),
                hovertemplate="<b>Time:</b> %{x}<br><b>Units:</b> %{y}<extra></extra>"
            )
        )
        # Solid segment for the rest of the forecast
        if len(x_data) > 2:
            figure.add_trace(
                pgo.Scatter(
                    x=x_data[1:],
                    y=y_data[1:],
                    mode="lines",
                    name="Forecast",
                    legendgroup="Forecast",
                    customdata=[forecast_trace_meta],
                    line=dict(color="red"),
                    hovertemplate="<b>Time:</b> %{x}<br><b>Units:</b> %{y}<extra></extra>"
                )
            )
    else:
        # Only forecast points, plot as solid
        figure.add_trace(
            pgo.Scatter(
                x=x_data,
                y=y_data,
                mode="lines",
                name="Forecast",
                customdata=[forecast_trace_meta],
                line=dict(color="red"),
                hovertemplate="<b>Time:</b> %{x}<br><b>Units:</b> %{y}<extra></extra>"
            )
        )
    # resize y-axis
    figure.update_yaxes(range=[0, max(y_data) * 1.2])

def plot_smoothed_curve(x_data, y_data, figure):
    """Adds a LOWESS curve trace to the figure that fits the given (x,y) data
    """
    numeric_x_data = [pd.Timestamp.toordinal(x) for x in x_data]
    lowess_smoothed = lowess(y_data, numeric_x_data, frac=0.1, it=0)
    lowess_x = [pd.Timestamp.fromordinal(
        int(x)) for x in lowess_smoothed[:, 0]]
    lowess_y = lowess_smoothed[:, 1]
    figure.add_trace(
        pgo.Scatter(
            x=lowess_x,
            y=lowess_y,
            mode="lines",
            name="Smoothed",
            showlegend=False,
            legendgroup="orders",
            line=dict(color="blue", width=5),
            # hovertemplate="<b>Time:</b> %{x}<br><b>Smoothed Units:</b> %{y}<extra></extra>",
        )
    )