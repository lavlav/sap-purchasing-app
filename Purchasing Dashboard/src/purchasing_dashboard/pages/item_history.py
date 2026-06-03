import dash
from dash import html
from purchasing_dashboard.layout.item_history.sidebar.sidebar import item_selection_sidebar
from purchasing_dashboard.layout.item_history.main_content import item_order_history_main_page_content



dash.register_page(__name__, path="/byItem", name="Item History and Forecasting")

layout = html.Div([
        item_selection_sidebar,
        item_order_history_main_page_content
    ], className="page-with-sidebar",)