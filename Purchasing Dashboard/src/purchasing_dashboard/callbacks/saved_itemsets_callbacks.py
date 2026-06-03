"""
Callbacks for saving and loading user-defined item sets.
"""

from datetime import datetime
from dash import ALL, ClientsideFunction, Input, Output, State, callback, clientside_callback, no_update, ctx

from purchasing_dashboard.layout.aio.user_data_menu_item import UserDataMenuItemAIO
import logging

from purchasing_dashboard.layout.item_history.sidebar.saved_itemsets_list import MAX_SAVED_ITEMSETS
from purchasing_dashboard.utils.callback_return_values import no_update_list
from purchasing_dashboard.utils.classnames import toggle_class

from purchasing_dashboard.utils.logging import logger

SAVE_SUCCESS_MESSAGE = "Itemset saved successfully."
SAVE_TOO_MANY_ITEMS_ERROR = "Too many saved itemsets."


@callback(
    Output(UserDataMenuItemAIO.ids.store(ALL), "data", allow_duplicate=True),
    Output("save-itemset-result-message", "children"),
    Input("save-itemset-button", "n_clicks"),
    State("save-itemset-result-message", "className"),
    State(UserDataMenuItemAIO.ids.store(ALL), "data"),
    State("item-code-filter", "value"),
    prevent_initial_call=True
)
def save_itemset(n_clicks, old_classname, current_data, item_codes):
    """
    Callback to save the selected item codes as a new itemset.
    """
    # TODO #74: Add logic to save to persistent storage (like a database or file)
    item_codes = item_codes or []
    if item_codes == []:
        logger.debug("No item codes selected, nothing to save.")
        return no_update_list(len(current_data) + 1)

    open_slot = -1
    for i in range(MAX_SAVED_ITEMSETS):
        if not current_data[i]:
            logger.debug(f"Saving itemset to slot {i}.")
            open_slot = i
            break
    if open_slot == -1:
        logger.warning("No available slot to save the itemset.")
        message = SAVE_TOO_MANY_ITEMS_ERROR
        return no_update_list(len(current_data)), message

    # Create a new itemset entry
    new_name = f"Set of {len(item_codes)} items"

    new_itemset = {
        "item_codes": item_codes,
        "menu_item_name": new_name,
        "timestamp": datetime.now().isoformat()
    }

    current_data[i] = new_itemset
    message = SAVE_SUCCESS_MESSAGE
    return current_data, message

# Client-side callback to handle the visibility of the save message
clientside_callback(
    ClientsideFunction(
        namespace='purchasing_dashboard',
        function_name='toggle_save_message_visibility'
    ),
    Output("save-itemset-result-message", "className"),
    Input("save-itemset-result-message", "children"),
    prevent_initial_call=True
)


@callback(
    Output("item-code-filter", "value"),
    Input(UserDataMenuItemAIO.ids.populate_button(ALL), "n_clicks"),
    State(UserDataMenuItemAIO.ids.populate_button(ALL), "id"),
    State(UserDataMenuItemAIO.ids.store(ALL), "data"),
    prevent_initial_call=True
)
def populate_item_codes(button_clicks, button_ids, saved_itemsets):
    """
    Populate the item codes filter with the codes from the selected saved itemset.
    """
    if not saved_itemsets:
        return no_update
    # Find the index of the button that was clicked
    if not ctx.triggered:
        return no_update
    index = -1
    for i, button_id in enumerate(button_ids):
        if ctx.triggered_id == button_id:
            logger.debug(f"Button {i} clicked, populating item codes.")
            index = i
            break
    if index == -1 or index >= len(saved_itemsets):
        logger.warning(
            "No valid button clicked or index out of range. Can't populate item codes.")
        return no_update
    return saved_itemsets[index].get("item_codes")


@callback(
    Output("save-itemset-button", "disabled"),
    Input("item-code-filter", "value")
)
def toggle_save_button(item_codes):
    """
    Enable or disable the save button based on whether any item codes are selected.
    """
    item_codes = item_codes or []
    if item_codes == []:
        return True
    return False
