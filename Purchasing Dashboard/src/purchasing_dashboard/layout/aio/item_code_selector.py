from dash import dcc, html
from frozendict import frozendict

from purchasing_dashboard.layout.common.store import ITEM_CODES_STORE_ID, STORE_TO_DEPENDENTS
import logging

from purchasing_dashboard.utils.logging import logger

# TODO #12: this can be generalized and reused for other dropdowns.
# TODO #74: should this have the loading inside the options instead of wrapping the whole thing?
class ItemCodeSelectorAIO(html.Div):
    """
    AIO component for the item code selector with loading state.

    """
    class ids:
        @staticmethod
        def loading(aio_id: str) -> dict:
            return {
                "aio_id": aio_id,
                "component": "item-code-selector",
                "subcomponent": "loading"
            }

    ids = ids

    def __init__(self, aio_id):
        loading_id = self.ids.loading(aio_id)
        logger.debug(f"Instantiating ItemCodeSelectorAIO with id {loading_id}")
        mapping = STORE_TO_DEPENDENTS.get(ITEM_CODES_STORE_ID, set())
        mapping.add(frozendict(loading_id))
        STORE_TO_DEPENDENTS[ITEM_CODES_STORE_ID] = mapping
        super().__init__([
            dcc.Loading(
                id=loading_id,
                type="dot",
                children=[
                    dcc.Dropdown(
                        id="item-code-filter",
                        placeholder="Select an Item Code",
                        multi=True,
                        searchable=True,
                        persistence=True,
                        maxHeight=200,
                        className="sidebar-dropdown",
                        closeOnSelect=False,
                    ),
                ],
                display="show" # unset later by callbacks
            )]
        )
