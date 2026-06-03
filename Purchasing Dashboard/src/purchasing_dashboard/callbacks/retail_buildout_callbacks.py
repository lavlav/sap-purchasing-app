from operator import call
from dash import Input, Output, State, callback, dcc, html, no_update

from purchasing_dashboard.layout.common.dropdown_labels import generate_option_label
from purchasing_dashboard.layout.common.store import PRODUCT_IDS_STORE_ID
from purchasing_dashboard.layout.product_buildout.buildout_table import BuildoutTable
from purchasing_dashboard.utils.api import api
from purchasing_dashboard.utils.classnames import toggle_hidden_class
from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.utils.info_messages import prompt_to_select_product

@callback(
    Output("product-dropdown", "options"),
    Input(PRODUCT_IDS_STORE_ID, "data"),
)
def update_product_dropdown(product_ids):
    if not product_ids:
        return []
    options = []
    for record in product_ids:
        option_label = generate_option_label(
            shorthand_code=record["ProductCode"],
            full_name=record["ProductName"],
            max_length=60,
            missing_full_name_placeholder="product name"
        )
        options.append(option_label)
    options.sort(key=lambda x: x["search"])
    return options

@callback(
    Output(BuildoutTable.ids.table("before-actions"), "data"),
    Output("buildout-info-message", "children"),
    Input("product-dropdown", "value")
)
def update_before_actions_table(selected_product):
    # Logic to update the before-actions table based on the selected product
    if not selected_product:
        return no_update, prompt_to_select_product
    # Fetch and return the relevant data for the before-actions table
    logger.debug(f"Selected product for before-actions table: {selected_product}")
    items = api.fetch_built_out_items(product_id=selected_product)
    # add Include field with default value 'true'
    for item in items:
        item['Include'] = 'true'
    # add the selected product as a row
    # logger.debug(f"Fetched items for before-actions table: {items}")
    return items, None

@callback(
    Output("buildout-info-message-container", "hidden"),
    Output("buildout-tables-container", "className"),
    Input("product-dropdown", "value"),
    State("buildout-tables-container", "className"),
)
def hide_buildout_info_message(selected_product, current_classname):
    value_selected = selected_product is not None
    classname = toggle_hidden_class(current_classname, not value_selected)
    return value_selected, classname

@callback(
    Output(BuildoutTable.ids.table("after-actions"), "data"),
    State(BuildoutTable.ids.table("before-actions"), "data"),
    State(BuildoutTable.ids.table("after-actions"), "data_timestamp"),
    State(BuildoutTable.ids.table("before-actions"), "data_timestamp"),
    Input("generate-buildout-button", "n_clicks"),
    prevent_initial_call=True
)
def update_after_actions_table(before_actions_data, after_actions_timestamp, before_actions_timestamp, n_clicks):
    raise NotImplementedError("Build-out computation not yet implemented.")