from dash import dcc, html
from frozendict import frozendict
import plotly.graph_objects as pgo

from purchasing_dashboard.layout.aio.tab_content_container import TabContentContainerAIO
from purchasing_dashboard.layout.common.store import CUSTOMER_BREAKDOWN_STORE_ID, STORE_TO_DEPENDENTS

n_visible_categories = 8

CUSTOMER_BREAKDOWN_CONTENT = html.Div([
    html.Div([
        dcc.Graph(
            id="customer-breakdown-bar-chart",
            figure=pgo.Figure(),
            config={
                "modeBarButtonsToRemove": ["zoom", "select", "pan", "lasso2d", "autoScale"],
            },
            className="item-history-graph"
        ),
    ], className="large-scrollable-container"),
    html.Div(
        id="customer-breakdown-sort-toggle-label",
        children=["Sort by: ", dcc.RadioItems(
            id="customer-breakdown-sort-toggle",
            options=[
                {"label": "Units", "value": "units"},
                {"label": "Sales", "value": "sales"}
            ],
            value="units",
            inline=True
        )]
    )
])

mapping = STORE_TO_DEPENDENTS.get(CUSTOMER_BREAKDOWN_STORE_ID, set())
mapping.add(frozendict(TabContentContainerAIO.ids.loading_wrapper("customer-breakdown-container")))
STORE_TO_DEPENDENTS[CUSTOMER_BREAKDOWN_STORE_ID] = mapping
