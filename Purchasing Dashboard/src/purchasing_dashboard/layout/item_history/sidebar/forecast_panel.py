from dash import html, dcc

from purchasing_dashboard.layout.aio.accordion import AccordionAIO
from purchasing_dashboard.layout.common.store import FORECAST_DATA_STORE_ID

from purchasing_dashboard.utils.info_messages import tooltip_pir_download_requirements, \
    forecasts_generated_info_template


def forecast_info_table_row(label, id, value=[]):
    return html.Div([
        html.Label(label, className="forecast-info-label"),
        html.Label(value, id=f"forecast-info-{id}",
                   className="forecast-info-value")
    ], className="forecast-info-row")


forecast_panel = html.Div(
    id="forecast-panel-container",
    children=[
        dcc.Store(id=FORECAST_DATA_STORE_ID, storage_type="session"),
        AccordionAIO(
            label="Forecasting",
            content=[
                html.Div([
                    dcc.Input(
                        id="forecast-time-horizon",
                        type="number",
                        value=10,
                        min=1,
                        max=100,
                        className="small-number-input",
                    ),
                    html.Label("Data Points", className="sidebar-plaintext")
                ], className="input-with-label"),
                dcc.Loading(id="forecast-type-loading",
                            children=[
                                dcc.Dropdown(
                                    id="forecast-type-dropdown",
                                    options=[],
                                    className="input-with-label",
                                    placeholder="Select Forecast Type")
                            ],
                            type="dot"),
                html.Button(
                    "Forecast", 
                    id="forecast-button",
                    className="important-button"
                ),
                html.Button(
                    "Forecast Together", 
                    id="forecast-together-button",
                    className="important-button"
                ),
                html.Label(
                    children=forecasts_generated_info_template.format(x=0, y=0),
                    id="forecasts-generated-info-label",
                    className="small-info-text"
                ),
                html.Div([
                    html.H3("Forecast Information"),
                    forecast_info_table_row(
                        "Time Initiated", "time-initiated"),
                    forecast_info_table_row(
                        "Points Forecasted", "time-horizon"),
                    forecast_info_table_row("Forecast Type", "forecast-type"),
                    html.Div([], id="forecast-info-goodness-of-fit"),
                ], id="forecast-info-subpanel", className="forecast-info-container hidden"),
                html.Div([
                    html.Button("Download PIR",
                                id="download-pir-button",
                                className="important-button download-button",
                                disabled=True
                                ),
                    dcc.Download(id="forecast-pir-download")
                ], className ="forecast-download-container",
                    title=tooltip_pir_download_requirements),
            ],
            aio_id="forecast-panel",
            initially_open=False
        )
    ], className="forecast-panel-container"),
