from dash import html
from purchasing_dashboard.layout.aio.item_code_selector import ItemCodeSelectorAIO
from purchasing_dashboard.layout.item_history.sidebar.forecast_panel import forecast_panel
from purchasing_dashboard.layout.item_history.sidebar.saved_itemsets_list import saved_itemsets_list
from purchasing_dashboard.utils.icons import Icons

item_code_selector = ItemCodeSelectorAIO("item-code-selector-loading")

item_selection_sidebar = html.Div([
    html.Div([
        html.Label([
            "Select Item Codes", 
            html.Span(
                id="save-itemset-result-message",
                className="save-itemset-result-message"
            ),
            html.Button(
                id="save-itemset-button",
                children=html.Img(src=Icons.SAVE.path),
                className="save-button menu-item-button",
                disabled=True
            )], className="sidebar-label"),
    ], className="sidebar-header"),
    item_code_selector,
    saved_itemsets_list,
    *forecast_panel
], className='sidebar-container')