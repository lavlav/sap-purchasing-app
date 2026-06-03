from typing import TypedDict
from dash import MATCH, Patch, ctx, html, dcc, callback, Input, Output, State, no_update
import pandas as pd
from purchasing_dashboard.layout.common.store import ITEM_CODES_STORE_ID
from purchasing_dashboard.utils.icons import Icons

from purchasing_dashboard.utils.logging import logger


class _ItemSelection(TypedDict):
    """
    Data structure to hold information about the current item selection.
    """
    n_items: int
    cur_item: int  # 1-indexed, 0 means "all items"
    item_names: list[str]

class _SelectionCache(TypedDict):
    current: str  # hash of current selection
    # dynamic keys: hash of frozenset of selected item codes -> _SelectionData

_ItemSelection.DEFAULT = _ItemSelection(
    n_items=0,
    cur_item=0,
    item_names=[]
)

class ItemSubselectorAIO(html.Div):
    """
    Subselector for items selected in the purchasing dashboard that displays
    individual item codes from the currently selected itemset.
    """

    class ids:
        @staticmethod
        def left_button(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "left-button",
                "component": "ItemSubselectorAIO"
            }

        @staticmethod
        def right_button(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "right-button",
                "component": "ItemSubselectorAIO"
            }

        @staticmethod
        def selected_item_name_h2(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "selected-item-name",
                "component": "ItemSubselectorAIO"
            }

        @staticmethod
        def navigation_label(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "navigation-label",
                "component": "ItemSubselectorAIO"
            }

        @staticmethod
        def store(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "store",
                "component": "ItemSubselectorAIO"
            }

    ids = ids

    def __init__(self, aio_id):
        left_button = html.Button(
            id=ItemSubselectorAIO.ids.left_button(aio_id),
            children=html.Img(src=Icons.LEFT_ARROW.path, className="icon"),
            className="menu-item-button arrow-button"
        )
        right_button = html.Button(
            id=ItemSubselectorAIO.ids.right_button(aio_id),
            children=html.Img(src=Icons.RIGHT_ARROW.path, className="icon"),
            className="menu-item-button arrow-button"
        )
        navigation_label = html.Label(
            children="",
            id=ItemSubselectorAIO.ids.navigation_label(aio_id),
            className="item-subselector-navigation-label",
        )
        item_name_label = html.H2("Item Name", id=ItemSubselectorAIO.ids.selected_item_name_h2(
            aio_id), className="selected-name header")
        center_div = html.Div([
            item_name_label,
            navigation_label,
        ], className="item-subselector-center")
        empty_key = str(hash(frozenset([])))
        initial_data = {
            empty_key: _ItemSelection.DEFAULT,
            "current": empty_key  # Unique hash for current selection
        }
        store = dcc.Store(id=ItemSubselectorAIO.ids.store(
            aio_id), storage_type="session", data=initial_data)
        super().__init__(
            id=aio_id,
            children=[
                store,
                left_button,
                center_div,
                right_button,
            ],
            className="item-subselector-header"
        )

    @callback(
        Output(ids.store(MATCH), "data", allow_duplicate=True),
        Input("item-code-filter", "value"),
        Input(ITEM_CODES_STORE_ID, "data"),
        State(ids.store(MATCH), "data"),
        prevent_initial_call=True
    )
    def update_store(selected_item_codes, all_item_codes, store_data):
        if not all_item_codes:
            logger.debug("No item codes available to update store.")
            return no_update
        selected_item_codes = selected_item_codes or []
        items_hash = str(hash(frozenset(selected_item_codes)))
        patch = Patch()
        patch["current"] = items_hash
        if store_data and store_data.get(items_hash):
            return patch
        df = pd.DataFrame.from_dict(all_item_codes)
        df = df[df["ItemCode"].isin(selected_item_codes)]
        # Sort by ItemName for consistent ordering
        df.sort_values(by="ItemName", inplace=True)
        n_items = len(selected_item_codes)

        selection_data = _ItemSelection(
            n_items=n_items,
            cur_item=0 if n_items != 1 else 1,   # show first item if only one selected
            item_names=df["ItemName"].tolist() if not df.empty else [],
        )
        patch[items_hash] = selection_data
        return patch

    @callback(
        Output(ids.selected_item_name_h2(MATCH), "children"),
        Input(ids.store(MATCH), "data")
    )
    def update_selected_item_name(store_data):
        if not store_data:
            logger.debug(
                "Store data is empty, cannot update selected item name.")
            return "No items selected."
        items_hash = store_data.get("current")
        cur_item = store_data.get(items_hash).get("cur_item")
        n_items = store_data.get(items_hash).get("n_items")
        if n_items == 0:
            return "No items selected."
        if cur_item > 0:
            return store_data[items_hash]["item_names"][cur_item - 1]
        return f"{n_items} items in selection"

    @callback(
        Output(ids.navigation_label(MATCH), "children"),
        Output(ids.navigation_label(MATCH), "hidden"),
        Input(ids.store(MATCH), "data")
    )
    def update_navigation_label(store_data: _SelectionCache):
        if not store_data:
            logger.debug(
                "Store data is empty, cannot update navigation label.")
            return None, True
        logger.debug(f"Item subselector has {len(store_data)} subsets.")
        items_hash = store_data.get("current")
        cur_item = store_data.get(items_hash).get("cur_item")
        n_items = store_data.get(items_hash).get("n_items")
        if cur_item > 0:
            return f"Item {cur_item} of {n_items}", False
        return None, True

    @callback(
        Output(ids.store(MATCH), "data", allow_duplicate=True),
        Input(ids.left_button(MATCH), "n_clicks"),
        Input(ids.right_button(MATCH), "n_clicks"),
        State(ids.store(MATCH), "data"),
        prevent_initial_call=True
    )
    def navigate_items(left_clicks, right_clicks, store_data: _SelectionCache):
        items_hash = store_data.get("current")
        if not items_hash:
            return no_update
        cur_item = store_data[items_hash].get("cur_item", 0)
        n_items = store_data[items_hash].get("n_items", 0)
        if n_items == 0:
            logger.debug("No items to navigate, returning no update.")
            return no_update
        if ctx.triggered_id.subcomponent == "left-button":
            cur_item = cur_item - 1 if cur_item > 0 else n_items
            logger.debug(
                f"Navigating to item {cur_item} of {n_items} after left button click {left_clicks}.")
        elif ctx.triggered_id.subcomponent == "right-button":
            cur_item = cur_item + 1 if cur_item < n_items else 0
            logger.debug(
                f"Navigating to item {cur_item} of {n_items} after right button click {right_clicks}.")
        store_data[items_hash]["cur_item"] = cur_item
        return store_data

    @callback(
        Output(ids.left_button(MATCH), "disabled"),
        Output(ids.right_button(MATCH), "disabled"),
        Input(ids.store(MATCH), "data"),
        prevent_initial_call=True
    )
    def toggle_navigation_buttons(store_data: _SelectionCache):
        if not store_data:
            logger.debug(
                "Store data is empty, cannot toggle navigation buttons.")
            return no_update
        items_hash = store_data.get("current")
        n_items = store_data.get(items_hash).get("n_items", 0)
        disabled = n_items <= 1
        return disabled, disabled
