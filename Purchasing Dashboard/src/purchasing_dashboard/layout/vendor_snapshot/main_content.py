from dash import html
from purchasing_dashboard.layout.vendor_snapshot.tables import vendor_items_purchased_table, open_orders_with_vendor_table

vendor_snapshot_main_content = html.Div([
    vendor_items_purchased_table,
    open_orders_with_vendor_table
], className="main-content-container double-table-container")