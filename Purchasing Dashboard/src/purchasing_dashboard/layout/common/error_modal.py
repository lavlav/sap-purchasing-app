from dash import MATCH, Input, Output, State, callback, html, dcc
from purchasing_dashboard.utils.classnames import toggle_hidden_class
from purchasing_dashboard.utils.environment_variables import MAINTAINER_CONTACT, MAINTAINER_CONTACT_LINK
from purchasing_dashboard.utils.icons import Icons
from purchasing_dashboard.utils.info_messages import content_error_modal


class ErrorModal(html.Div):
    class ids:
        @staticmethod
        def container(aio_id="error-modal"):
            return {"aio_id": aio_id, "component": "ErrorModal", "subcomponent": "container"}

        @staticmethod
        def close_button(aio_id="error-modal"):
            return {"aio_id": aio_id, "component": "ErrorModal", "subcomponent": "close-button"}

        @staticmethod
        def exception_text(aio_id="error-modal"):
            return {"aio_id": aio_id, "component": "ErrorModal", "subcomponent": "exception-text"}

    def __init__(self, aio_id="error-modal"):
        if MAINTAINER_CONTACT_LINK:
            maintainer_contact_info = html.A(
                href=MAINTAINER_CONTACT_LINK,
                children=MAINTAINER_CONTACT,
                target="_blank",
                rel="noopener noreferrer"
            )
        else:
            maintainer_contact_info = MAINTAINER_CONTACT
        info_text = content_error_modal.copy()
        info_text.insert(1, maintainer_contact_info)
        super().__init__(
            children=[
                html.Label(
                    children=info_text,
                    className="error-modal-content"),
                html.Label(
                    children="Exception Text",
                    className="exception-text",
                    id=ErrorModal.ids.exception_text(aio_id)),
                html.Button(
                    children=html.Img(
                        src=Icons.DELETE.path, className="icon icon-delete"),
                    id=ErrorModal.ids.close_button(aio_id),
                    n_clicks=0,
                    className="delete-button"),
            ],
            id=ErrorModal.ids.container(aio_id),
            hidden=True,
            className="error-modal hidden",
        )

    ids = ids

    @callback(
        Output(ids.container(MATCH), "className"),
        State(ids.container(MATCH), "className"),
        Input(ids.close_button(MATCH), "n_clicks"),
        prevent_initial_call=True
    )
    def close_modal(old_classname, _):
        return toggle_hidden_class(old_classname, True)


error_modal = ErrorModal("error-modal")
