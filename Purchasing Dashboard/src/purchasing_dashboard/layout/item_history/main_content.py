from dash import html, dcc
from purchasing_dashboard.layout.item_history.tabs.tabs_container import item_history_tabs
from purchasing_dashboard.layout.item_history.summary_header import item_order_summary_header

item_order_history_main_page_content = html.Div([
    item_order_summary_header,
    item_history_tabs
], className="main-content-container")