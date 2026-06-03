from dash import MATCH, Input, Output, State, callback, ctx, html, no_update

from purchasing_dashboard.utils.classnames import toggle_hidden_class
from purchasing_dashboard.utils.logging import logger

CLOSED_SYMBOL = "+"
OPEN_SYMBOL = "–" # Represents the closed and open states of the accordion

class AccordionAIO(html.Div):
    """
    AIO Accordion component for displaying a subpanel in a collapsible format.
    """
    class ids:
        @staticmethod
        def subpanel_container(id):
            return {
                "aio_id": id,
                "subpanel_container": f"accordion-subpanel-container"
            }

        @staticmethod
        def label(id):
            return {
                "aio_id": id,
                "label": f"accordion-label"
            }

        @staticmethod
        def open_indicator(id):
            return {
                "aio_id": id,
                "open_indicator": f"accordion-open-indicator"
            }

        @staticmethod
        def header(id):
            return {
                "aio_id": id,
                "header": f"accordion-header"
            }

    def __init__(self, label, aio_id, content=None, className=None, initially_open=True):
        label = html.Span(label, id=self.ids.label(aio_id), className="accordion-header-text accordion-header-label")
        symbol = OPEN_SYMBOL if initially_open else CLOSED_SYMBOL
        open_indicator = html.Span(
            symbol, id=self.ids.open_indicator(aio_id), className="accordion-header-text")
        header = html.Div(
            id=self.ids.header(aio_id),
            children=[
                label,
                open_indicator
            ],
            className="accordion-header",
        )
        content_container = html.Div(
            id=self.ids.subpanel_container(aio_id),
            className=toggle_hidden_class("accordion-subpanel-container", not initially_open),
            children=content or []
        )
        super().__init__(
            children=[header, content_container],
            className=className or "accordion-container"
        )

    # #74: make this a clientside callback
    @callback(
        Output(ids.open_indicator(MATCH), "children"),
        Output(ids.subpanel_container(MATCH), "className"),
        State(ids.open_indicator(MATCH), "children"),
        State(ids.subpanel_container(MATCH), "className"),
        State(ids.header(MATCH), "id"),
        Input(ids.header(MATCH), "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_accordion(open_indicator, subpanel_container, header_id, _):
        logger.debug(f"Toggling accordion with header id: {header_id}")
        if ctx.triggered_id == header_id:
            new_open_indicator = OPEN_SYMBOL if open_indicator == CLOSED_SYMBOL else CLOSED_SYMBOL
            new_classname = toggle_hidden_class(
                subpanel_container, new_open_indicator == CLOSED_SYMBOL)
            return new_open_indicator, new_classname
        return no_update, no_update
