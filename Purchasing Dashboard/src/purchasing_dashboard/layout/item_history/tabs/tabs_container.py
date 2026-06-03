from dash import html, dcc
from purchasing_dashboard.layout.aio.tab_content_container import TabContentContainerAIO
from purchasing_dashboard.layout.common.store import ALL_ORDERS_DATA_STORE_ID, FORECAST_DATA_STORE_ID, ITEM_CODES_STORE_ID, ORDER_HISTORY_DATA_STORE_ID
from purchasing_dashboard.layout.item_history.tabs.customer_breakdown import CUSTOMER_BREAKDOWN_CONTENT
from purchasing_dashboard.layout.item_history.tabs.historic_demand_plot import HISTORIC_DEMAND_SUMMARY_PLOT_CONTENT
from purchasing_dashboard.layout.item_history.tabs.item_order_history_table import ITEM_ORDER_HISTORY_CONTENT
from purchasing_dashboard.layout.item_history.tabs.historic_usage_table import DEMAND_SUMMARY_TABLE_CONTENT
from purchasing_dashboard.layout.item_history.tabs.price_point_analysis import PRICE_POINT_ANALYSIS_CONTENT
from purchasing_dashboard.layout.item_history.tabs.projected_coverage import PROJECTED_COVERAGE_PANEL
from purchasing_dashboard.utils.info_messages import prompt_to_select_item_from_sidebar

item_history_tabs = html.Div([
    html.Div([
        html.Label("Select Time Interval:", style={"fontWeight": "bold"}),
        dcc.RadioItems(
            id="time-interval-picker",
            options=[
                {"label": "Daily", "value": "day"},
                {"label": "Weekly", "value": "week"},
                {"label": "Monthly", "value": "month"},
                {"label": "Quarterly", "value": "quarter"},
                {"label": "Yearly", "value": "year"},
            ],
            value="month",
            inline=True,
            persistence=True,
            persistence_type="memory",
        ),
    ], className="time-interval-picker-container"),
    dcc.Tabs(id="tabs", value="historic-demand-plot-tab", children=[
        dcc.Tab(label="Demand Summary Plot",
                value="historic-demand-plot-tab",
                children=TabContentContainerAIO(
                    aio_id="historic-demand-plot-container",
                    content=HISTORIC_DEMAND_SUMMARY_PLOT_CONTENT,
                    data_dependencies=[
                        ORDER_HISTORY_DATA_STORE_ID, FORECAST_DATA_STORE_ID],
                    has_time_bucket_dependency=True,
                    target_components={
                        "historic-demand-plot-container": "children", "historic-demand-plot": "figure"}
                ),
                className="item-history-tab"
                ),
        dcc.Tab(label="Demand Summary Table",
                value="hist-usage-table-tab",
                children=TabContentContainerAIO(
                    aio_id="hist-usage-table-container",
                    content=DEMAND_SUMMARY_TABLE_CONTENT,
                    data_dependencies=[ORDER_HISTORY_DATA_STORE_ID],
                    has_time_bucket_dependency=True
                ),
                className="item-history-tab"
                ),
        dcc.Tab(label="Customer Breakdown",
                value="customer-breakdown-tab",
                children=TabContentContainerAIO(
                    aio_id="customer-breakdown-container",
                    content=CUSTOMER_BREAKDOWN_CONTENT,
                    data_dependencies=[ORDER_HISTORY_DATA_STORE_ID],
                    has_time_bucket_dependency=False
                ),
                className="item-history-tab"
                ),
        dcc.Tab(label="Recent Item Order History",
                value="order-hist-table-tab",
                children=TabContentContainerAIO(
                    aio_id="order-hist-table-container",
                    content=ITEM_ORDER_HISTORY_CONTENT,
                    data_dependencies=[ALL_ORDERS_DATA_STORE_ID],
                    has_time_bucket_dependency=False
                ),
                className="item-history-tab"
                ),
        dcc.Tab(label="Price Point Analysis",
                value="price-point-analysis-tab",
                children=TabContentContainerAIO(
                    aio_id="price-point-analysis-container",
                    content=PRICE_POINT_ANALYSIS_CONTENT,
                    data_dependencies=[ALL_ORDERS_DATA_STORE_ID, ITEM_CODES_STORE_ID],
                    has_time_bucket_dependency=False
                ),
                className="item-history-tab"
                ),
        dcc.Tab(label="Projected Coverage",
                value="projected-coverage-tab",
                children=TabContentContainerAIO(
                    aio_id="projected-coverage-container",
                    content=PROJECTED_COVERAGE_PANEL,
                    data_dependencies=[ORDER_HISTORY_DATA_STORE_ID],
                    has_time_bucket_dependency=True
                ),
                className="item-history-tab"
                ),
    ],
        persistence=True,
        persistence_type="session",
        persisted_props=["value"]
    ),
    html.Div(id="no-item-selected-info-div", children=[
                html.Label(prompt_to_select_item_from_sidebar,
                           className="info-text")
    ],
        className="centered-flex-container"
    )

]
)
