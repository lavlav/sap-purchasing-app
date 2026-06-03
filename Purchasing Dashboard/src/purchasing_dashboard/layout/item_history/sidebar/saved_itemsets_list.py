from dash import html, dcc

from purchasing_dashboard.layout.aio.accordion import AccordionAIO
from purchasing_dashboard.layout.aio.user_data_menu_item import UserDataMenuItemAIO

MAX_SAVED_ITEMSETS = 10

saved_itemsets_list = AccordionAIO(
    label="Saved Itemsets",
    content=html.Div([
        UserDataMenuItemAIO(
            aio_id=f"saved-itemset-{i}", 
            storage_type="local"
            ) 
            for i in range(MAX_SAVED_ITEMSETS)
    ], className="sidebar-menu-items-container"),
    aio_id="saved-itemsets-accordion",
    initially_open=True
)
