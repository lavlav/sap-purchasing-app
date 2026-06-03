from dash import html, dcc

from purchasing_dashboard.layout.common.store import PRODUCT_IDS_STORE_ID, STORE_TO_DEPENDENTS
from purchasing_dashboard.layout.product_buildout.buildout_table import BuildoutTable
from purchasing_dashboard.layout.product_buildout.buildout_actions_table import BuildoutActionsTable

# TODO #41: Implement retail buildout dashboard
retail_buildout_main_content = html.Div([
    html.H2("Retail Build-Out (WIP)",
            className="main-content-header"),
    dcc.Loading(
        id="product-dropdown-loading",
        children=[
            dcc.Dropdown(
                id="product-dropdown",
                placeholder="Select a Product",
                persistence=True,
            ),
        ],
        parent_className="dropdown-container",
        display="show",
        type="dot"
    ),
    html.Div(
        id="buildout-tables-container",
        children=[
            BuildoutTable("before-actions"),
            BuildoutActionsTable("buildout-actions"),
            BuildoutTable("after-actions"),
        ],
        className="buildout-tables-container horizontal-flex"
    ),
    html.Div(
        id="buildout-info-message-container",
        children=[
        html.Label(
            children=[],
            id="buildout-info-message",
            className="info-text"),
    ], className="centered-info-text-container"),
    html.Button("Compute Build-Out Actions", id="generate-buildout-button",
                className="important-button")
], className="main-content-container vertical-flex")

# Register loading wrapper for product IDs store
mapping = STORE_TO_DEPENDENTS.get(PRODUCT_IDS_STORE_ID, set())
if mapping == set():
    mapping.add("product-dropdown-loading")
STORE_TO_DEPENDENTS[PRODUCT_IDS_STORE_ID] = mapping
