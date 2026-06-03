import dash
from dash import html
from purchasing_dashboard.layout.vendor_snapshot.sidebar import filter_sidebar
from purchasing_dashboard.layout.vendor_snapshot.tables import vendor_items_purchased_table, open_orders_with_vendor_table

dash.register_page(__name__, path="/", name="Landing")

layout = html.Div([
        # TODO #70: Get user name and personalize this to users
        html.H3("Hello! This is the dashboard home page. Click a link above to get started.")
    ], className="page"
)