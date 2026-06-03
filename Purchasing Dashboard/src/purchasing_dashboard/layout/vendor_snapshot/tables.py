from dash import html, dash_table, dcc
from purchasing_dashboard.utils.placeholder_data import generate_placeholder_table_data

#Visible column names
VENDOR_ITEMS_PURCHASED_TABLE_COLUMNS = ["Vendor Code", "Vendor Name", "Item Code", "Item Name", "Working Days On Hand", "On Order"]

vendor_items_purchased_table = html.Div([
    html.H3("Items Purchased from Vendor"),
    dcc.Loading(
        id="loading-vendor-items-purchased-table",
        overlay_style={"visibility":"visible","filter":"blur(2px)"},
        children=[
            dash_table.DataTable(
                id='vendor-items-purchased-table',
                columns=[{"name": col, "id": col.replace(" ", "")}
                         for col in VENDOR_ITEMS_PURCHASED_TABLE_COLUMNS],
                data=generate_placeholder_table_data(VENDOR_ITEMS_PURCHASED_TABLE_COLUMNS),
                page_size=10,
                sort_action='native',
                sort_mode='multi',
                persistence=True,
                persistence_type='session',
                persisted_props=['data', 'columns.name', 'filter_query', 'hidden_columns', 'page_current', 'selected_columns', 'selected_rows', 'sort_by']
        ),
        ],
        display="show"
    ),
    dcc.Store(id="vendor-items-purchased-table-loaded", storage_type='session', data=False)
], className="vendor-snapshot-table-container")

#Visible column names
OPEN_ORDERS_TABLE_COLUMNS = ["Vendor Code", "Item Code", "Item Name", "PO Number", "Line Status", "Due Date", "Quantity Ordered", "Comments"]

open_orders_with_vendor_table = html.Div([
    html.H3("Open Orders with Vendor"),
    dcc.Loading(
        id="loading-open-orders-table",
        overlay_style={"visibility":"visible","filter":"blur(2px)"},
        children=[
            dash_table.DataTable(
                id='open-orders-with-vendor-table',
                columns=[{"name": col, "id": col.replace(" ","")}
                         for col in OPEN_ORDERS_TABLE_COLUMNS],
                data=generate_placeholder_table_data(OPEN_ORDERS_TABLE_COLUMNS),
                page_size=10,
                sort_action='native',
                sort_mode='multi', 
                persistence=True,
                persistence_type='session',
                persisted_props=['data', 'columns.name', 'filter_query', 'hidden_columns', 'page_current', 'selected_columns', 'selected_rows', 'sort_by']
            ),
        ],
        display="show"
    ),
    dcc.Store(id="open-orders-with-vendor-table-loaded", data=False)
], className="vendor-snapshot-table-container")
