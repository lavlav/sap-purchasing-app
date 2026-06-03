from datetime import datetime
from zoneinfo import ZoneInfo
from dash import Input, Output, State, callback, ctx, no_update
from dashboard_common.model.time_bucket import TimeBucket
from purchasing_dashboard.layout.common.store import FORECAST_DATA_STORE_ID, get_dependent_outputs_for_store
from purchasing_dashboard.layout.item_history.sidebar.forecast_panel import forecast_info_table_row
from purchasing_dashboard.utils.callback_return_values import no_update_tuple
from purchasing_dashboard.utils.environment_variables import TIMEZONE
from purchasing_dashboard.utils.info_messages import (placeholder_text_forecast_type_dropdown_unavailable,
                                                              placeholder_text_forecast_type_dropdown_available)
from dashboard_common.model.forecast import Forecast, ForecastSet, ForecastType
from purchasing_dashboard.utils.api import api
import pandas as pd
from purchasing_dashboard.utils.info_messages import forecasts_generated_info_template

from purchasing_dashboard.utils.classnames import add_if_not_present, toggle_hidden_class

from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.utils.string_manipulation import to_time_ago_string


@callback(
    Output("forecast-panel-container", "className"),
    State("forecast-panel-container", "className"),
    Input("item-code-filter", "value"),
)
def disable_forecast_panel(classname, item_codes: list[str]):
    """
    Disable the forecast panel if no item code is selected.
    """
    item_codes = item_codes or []
    if item_codes == []:
        return add_if_not_present(classname, "hidden")
    else:
        return classname.replace("hidden", "").strip()


@callback(
    Output(FORECAST_DATA_STORE_ID, "data"),
    State(FORECAST_DATA_STORE_ID, "data"),
    State("item-code-filter", "value"),
    State("time-interval-picker", "value"),
    State("forecast-type-dropdown", "value"),
    State("forecast-time-horizon", "value"),
    Input("forecast-button", "n_clicks"),
    Input("forecast-together-button", "n_clicks"),
    background=True,
    running=[
        *get_dependent_outputs_for_store(FORECAST_DATA_STORE_ID),
        (Output("forecast-button", "disabled"), True, False),
        (Output("forecast-together-button", "disabled"), True, False)
    ],
    prevent_initial_call=True
)
def generate_forecast(existing_data, item_codes: list[str], period, forecast_type, n_forecasts, _, __):
    """
    Generate a forecast for the selected item code.
    """
    if not item_codes or len(item_codes) == 0:
        return no_update
    if ctx.triggered_id == "forecast-button":
        individual_forecasts = True
    elif ctx.triggered_id == "forecast-together-button":
        individual_forecasts = False
    else:
        logger.error(f"Unexpected trigger id: {ctx.triggered_id}")
        return no_update

    if not forecast_type:
        logger.warning("No forecast type selected. Defaulting to 'auto'.")
        forecast_type = "auto"

    logger.debug(
        f"Existing data for items {item_codes} in period {period}: {existing_data}")
    fs = ForecastSet.from_dict(
        existing_data) if existing_data else ForecastSet()

    logger.info(
        f"Requesting forecast for item codes: {item_codes} with type: {forecast_type} and batch mode: {not individual_forecasts}")

    # Fetch forecast data
    if individual_forecasts:
        # TODO #74: add batch mode toggling on the API side
        forecast_data_list = [
            (
                item,
                api.fetch_order_forecast(
                    [item], period, n_forecasts, forecast_type)
            ) for item in item_codes]
    else:
        forecast_data_list = [
            (
                item_codes,
                api.fetch_order_forecast(
                    item_codes, period, n_forecasts, forecast_type)
            )
        ]
    for items, forecast_data in forecast_data_list:
        # Convert to DataFrame
        df = pd.DataFrame(forecast_data["predictions"])
        goodness_of_fit = forecast_data.get("goodness_of_fit", {})
        time_calculated = forecast_data["calculated_at"]
        received_forecast_type = forecast_data["forecast_type"]

        forecast = Forecast(
            item_codes=items,
            time_bucket=period,
            time_initiated=datetime.now(ZoneInfo(TIMEZONE)),
            time_computed=datetime.fromtimestamp(time_calculated),
            num_forecasted_points=n_forecasts,
            initiated_type=ForecastType[forecast_type],
            received_type=ForecastType[received_forecast_type].value,
            goodness_of_fit=goodness_of_fit,
            forecast_data=df
        )

        fs.put(forecast)
        logger.info(
            f"Received forecast for item {items} in period {period}: {forecast}")

    return fs.to_dict()


@callback(
    Output("forecast-info-subpanel", "className"),
    Output("forecast-info-time-initiated", "children"),
    Output("forecast-info-time-initiated", "title"),
    Output("forecast-info-time-horizon", "children"),
    Output("forecast-info-forecast-type", "children"),
    Output("forecast-info-goodness-of-fit", "children"),
    State("forecast-info-subpanel", "className"),
    Input(FORECAST_DATA_STORE_ID, "data"),
    Input("item-code-filter", "value"),
    Input("time-interval-picker", "value")
)
def display_forecast_info(forecast_info_class, forecast_data, item_ids, time_bucket):
    """
    Update the forecast information display based on the selected item and time bucket.
    """
    def hide():
        return toggle_hidden_class(forecast_info_class, True), no_update, no_update, no_update, no_update, no_update

    if not forecast_data or not item_ids:
        return hide()

    forecast = ForecastSet.from_dict(forecast_data).get(item_ids, time_bucket)
    if forecast is None:
        logger.warning(
            "Forecast data is empty, cannot update forecast information.")
        return hide()

    # Mention if the forecast was chosen as "auto"
    if forecast.initiated_type == ForecastType.auto:
        forecast_type_display = f"(Automatic) {forecast.received_type.get_display_name()}"
    else:
        forecast_type_display = forecast.initiated_type.get_display_name()

    # Show the goodness of fit metrics
    goodness_of_fit = [forecast_info_table_row(metric, f"goodness-of-fit-{metric}", round(
        value, 2)) for metric, value in forecast.goodness_of_fit.items() if value is not None]

    # Backwards compatibility with older forecasts whose time_initiated may not have timezone info
    if forecast.time_initiated.tzinfo is None:
        time_initiated = forecast.time_initiated.replace(
            tzinfo=ZoneInfo(TIMEZONE))
    else:
        time_initiated = forecast.time_initiated

    return (
        toggle_hidden_class(forecast_info_class, False),
        to_time_ago_string(time_initiated),
        time_initiated.strftime("%Y-%m-%d %H:%M:%S"),
        forecast.num_forecasted_points,
        forecast_type_display,
        goodness_of_fit
    )


@callback(
    Output("forecast-type-dropdown", "options"),
    Output("forecast-type-dropdown", "disabled"),
    Output("forecast-type-dropdown", "placeholder"),
    Input("item-code-filter", "value"),
    background=True
)
def update_forecast_type_dropdown(item_codes: list[str]) -> tuple[list[dict], bool, str]:
    """
    Update the forecast type dropdown options based on the selected item codes.
    """
    if not item_codes or len(item_codes) == 0:
        return [], True, placeholder_text_forecast_type_dropdown_unavailable

    # Fetch available forecast types for the selected items
    response = api.fetch_available_forecast_types(item_codes)

    if not response["forecast_types"]:
        return [], True, placeholder_text_forecast_type_dropdown_unavailable

    available_types = response["forecast_types"]
    options = [{"label": ForecastType[ftype].get_display_name(), "value": ftype}
               for ftype in available_types]
    return options, False, placeholder_text_forecast_type_dropdown_available


@callback(
    Output("forecast-button", "disabled"),
    Output("forecast-together-button", "disabled"),
    Input("forecast-type-dropdown", "value"),
)
def disable_forecast_button(selected_type: str) -> bool:
    """
    Disable the forecast buttons if no forecast types are selected or available.
    """
    if not selected_type or len(selected_type) == 0:
        return True, True
    return False, False


@callback(
    Output("forecast-button", "children"),
    Output("forecast-together-button", "hidden"),
    Output("forecasts-generated-info-label", "children"),
    Input("item-code-filter", "value"),
    Input(FORECAST_DATA_STORE_ID, "data"),
    Input("time-interval-picker", "value"),
)
def update_forecast_buttons(item_codes: list[str], forecast_data: dict, time_interval: str) -> tuple[str, bool]:
    """
    Update the forecast button text and visibility of the multiple forecast button
    based on the number of selected item codes.
    """
    logger.debug(
        f"Updating forecast buttons for item codes: {item_codes} with forecast data: {forecast_data} and time interval: {time_interval}")
    if not item_codes or len(item_codes) == 0:
        return "Forecast", True, None
    n_item_codes = len(item_codes)
    if n_item_codes == 1:
        return "Forecast", True, None
    else:
        time_bucket = TimeBucket[time_interval]
        n_individual_forecasts = 0
        if forecast_data is not None:
            for item in item_codes:
                if ForecastSet.from_dict(forecast_data).get([item], time_bucket) is not None:
                    n_individual_forecasts += 1
        info_str = forecasts_generated_info_template.format(
            x=n_individual_forecasts, y=n_item_codes)
        return "Forecast Individual", False, info_str
