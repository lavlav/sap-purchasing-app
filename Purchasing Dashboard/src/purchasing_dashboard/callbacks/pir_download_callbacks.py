from dash import callback, Output, Input, State, no_update, dcc
from dashboard_common.model.forecast import ForecastSet, Forecast
from dashboard_common.model.time_bucket import TimeBucket
from purchasing_dashboard.layout.common.store import FORECAST_DATA_STORE_ID

from purchasing_dashboard.utils.pir import generate_pir_dataframe

from purchasing_dashboard.utils.logging import logger

@callback(
    Output("download-pir-button", "disabled"),
    Input("item-code-filter", "value"),
    Input(FORECAST_DATA_STORE_ID, "data")
)
def toggle_pir_download_button(item_ids, forecast_data):
    """
    Toggle the visibility of the download button if there is monthly forecast data.
    """
    if not item_ids or not forecast_data:
        logger.debug("No item codes selected or no forecast data available. Hiding download button.")
        return True
    forecast_set = ForecastSet.from_dict(forecast_data)
    for item_id in item_ids:
        if not forecast_set.get(item_id, TimeBucket.month):
            logger.debug(f"No monthly forecast data for item {item_id}. Hiding download button.")
            return True
    return False

@callback(
    Output("forecast-pir-download", "data"),
    State(FORECAST_DATA_STORE_ID, "data"),
    State("item-code-filter", "value"),
    Input("download-pir-button", "n_clicks"),
    prevent_initial_call=True
)
def upload_pir_to_user(forecast_data, item_codes, n_clicks):
    """
    Generate a PIR (Planned Independent Requirements) file for the selected item.
    """
    if not forecast_data or not item_codes:
        return no_update
    
    forecast_set = ForecastSet.from_dict(forecast_data)
    forecast = forecast_set.get(item_codes, "month")

    if not forecast:
        logger.warning(
            f"User requested report for {item_codes}, but no forecast data is available.")
        return no_update

    # Generate the PIR report
    try:
        pir_report = generate_pir_dataframe(item_codes, forecast_set, num_months=10)
    except Exception as e:
        logger.error(f"Error generating PIR report: {e}")
        logger.debug(f"Forecast data: {forecast_data}")
        return no_update
    
    n_items = len(item_codes)
    if n_items < 3:
        suffix = '_'.join(item_codes)
    else:
        item_codes = sorted(item_codes)
        suffix = f"{item_codes[0]}_{item_codes[1]}_plus_{n_items - 2}_others"

    return dcc.send_data_frame(
        pir_report.to_csv,
        filename=f"pir_report_{suffix}.csv",
        index=False
    )