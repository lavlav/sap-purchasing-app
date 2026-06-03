import dash
from dash import html
from purchasing_dashboard.layout.vendor_snapshot.sidebar import filter_sidebar
from purchasing_dashboard.layout.vendor_snapshot.main_content import vendor_snapshot_main_content

dash.register_page(__name__, path="/vendorSnapshot", name="Vendor Snapshot")

layout = html.Div([
        filter_sidebar,
        vendor_snapshot_main_content
    ], className="page-with-sidebar")