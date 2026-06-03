import json
from dash import MATCH, Input, Output, State, callback, ctx, html, dcc, no_update

from purchasing_dashboard.utils.classnames import toggle_class, toggle_hidden_class
from purchasing_dashboard.utils.icons import Icons

import logging

from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.utils.string_manipulation import stringify_dash_id


class UserDataMenuItemAIO(html.Div):
    """
    Basic AIO component for user data menu items.
    Data can be persisted locally or server-side.
    The "X" button is used to delete the item.
    """
    class ids:
        @staticmethod
        def input(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "label",
                "component": "UserDataMenuItemAIO"
            }

        @staticmethod
        def store(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "store",
                "component": "UserDataMenuItemAIO"
            }

        @staticmethod
        def delete_button(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "delete-button",
                "component": "UserDataMenuItemAIO"
            }

        @staticmethod
        def populate_button(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "populate-button",
                "component": "UserDataMenuItemAIO"
            }

        @staticmethod
        def container(aio_id):
            return {
                "aio_id": aio_id,
                "subcomponent": "container",
                "component": "UserDataMenuItemAIO"
            }

    ids = ids

    def __init__(self, aio_id, storage_type):
        logger.debug(
            f"Creating UserDataMenuItemAIO with ID: {aio_id}, storage type: {storage_type}")
        store_storage_type = "local" if storage_type == "local" else "session"
        super().__init__(
            id=self.ids.container(aio_id),
            children=[
                dcc.Store(id=self.ids.store(aio_id),
                          storage_type=store_storage_type),
                html.Div(children=[
                    html.Label([
                       html.Img(
                           src=Icons.EDIT_PENCIL.path,
                       ),
                    ],
                    htmlFor=stringify_dash_id(self.ids.input(aio_id)),
                    className="editable-indicator icon"),
                    dcc.Input(
                        id=self.ids.input(aio_id),
                        value=None,
                        type="text",
                        inputMode="verbatim",
                        maxLength=80,
                        spellCheck=True,
                        persistence=True,
                        persistence_type=store_storage_type,
                        className="sidebar-input"),
                    html.Div([
                        html.Button(id=self.ids.populate_button(aio_id), children=[
                            html.Img(src=Icons.CORNER_RIGHT_UP.path,
                                     className="populate-button icon")
                        ], className="populate-button menu-item-button"),
                        html.Button(id=self.ids.delete_button(aio_id), children=[
                            html.Img(src=Icons.TRASH.path,
                                     className="delete-button icon")
                        ], className="delete-button menu-item-button")
                    ])
                ],
                className="sidebar-menu-item-container sidebar-menu-item"),
            ]
        )

    @callback(
        Output(ids.container(MATCH), "className"),
        State(ids.container(MATCH), "className"),
        Input(ids.store(MATCH), "data"),
    )
    def update_visibility(class_name, data):
        """
        Update the visibility of the menu item based on the presence of data.
        If data is present, show the item; otherwise, hide it.
        """
        return toggle_hidden_class(class_name, data is None)

    @callback(
        Output(ids.input(MATCH), "value"),
        Output(ids.store(MATCH), "data", allow_duplicate=True),
        Input(ids.input(MATCH), "value"),
        Input(ids.store(MATCH), "data"),
        prevent_initial_call=True
    )
    def update_label(label, data):
        """
        Circular callback:
        If the data was updated (e.g., item codes were saved),
        update the label text based on the stored data.
        If the label was updated (e.g., user edited the label),
        update the stored data with the new label text.
        """
        if ctx.triggered_id["subcomponent"] == "label":
            # User edited the label
            if data:
                data["menu_item_name"] = label
                return no_update, data
            else:
                logger.warning(
                    "User appears to have edited label, but no data is available.")
                return no_update, None
        else:
            # Data was updated (e.g., item codes were saved)
            if data:
                # Return the name from the data
                return data.get("menu_item_name", ""), no_update
            else:
                return "", no_update

    @callback(
        Output(ids.store(MATCH), "data", allow_duplicate=True),
        Input(ids.delete_button(MATCH), "n_clicks"),
        prevent_initial_call=True
    )
    def delete_item(n_clicks):
        """
        Delete the menu item by clearing its data.
        """
        if n_clicks:
            return None
        return no_update
