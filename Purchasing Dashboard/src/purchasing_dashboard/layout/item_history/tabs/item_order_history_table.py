from dash import html, dcc, dash_table
from purchasing_dashboard.layout.common.inline_styles import INLINE_ITEM_HISTORY_TABLE_CELL_STYLE
from purchasing_dashboard.utils.placeholder_data import generate_placeholder_table_data

ITEM_ORDER_HISTORY_TABLE_COLUMNS = ["Item Code", "Vendor Name", "PO Number", "Line Status", "Order Date",
                                    "Due Date", "Delivery Date", "Quantity Ordered", "Quantity Received", "Price", "Comments"]

ITEM_ORDER_HISTORY_CONTENT = html.Div([
        dash_table.DataTable(
            id="item-order-history-table",
            columns=[{"name": col, "id": col.replace(" ", "")} for col in ITEM_ORDER_HISTORY_TABLE_COLUMNS],
            data=generate_placeholder_table_data(ITEM_ORDER_HISTORY_TABLE_COLUMNS),
            page_size=10,
            sort_action='native',
            sort_mode='multi',
            #filter_action='native',
            #filter_options={"case": "insensitive", "placeholder": "Enter value to filter by"},
            persistence=True,
            persistence_type='session',
            persisted_props=['data', 'columns.name', 'filter_query', 'hidden_columns',
                             'page_current', 'selected_columns', 'selected_rows', 'sort_by'],
            style_cell=INLINE_ITEM_HISTORY_TABLE_CELL_STYLE
        )
    ], className="item-order-history-table-container")

