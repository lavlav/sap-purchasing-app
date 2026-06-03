from dash import html

from purchasing_dashboard.layout.aio.accordion import AccordionAIO

_MAX_ACTIONS = 15

class BuildoutActionsTable(html.Div):
    """A DataTable for displaying product buildout actions."""

    class ids:
        @staticmethod
        def table(aio_id: str):
            return {
                "component": "BuildoutActionsTable",
                "subcomponent": "table",
                "aio_id": aio_id
            }
        
    ids = ids

    def __init__(self, aio_id: str):
        children = [
            AccordionAIO(
                aio_id=f"buildout-actions-accordion-{i}", 
                label=f"Buildout Action {i}",
                content=[
                    html.Div("Action details will be displayed here.")
                ],
                initially_open=False
            ) for i in range(_MAX_ACTIONS)
        ]
        super().__init__(
            children=children,
            className="buildout-actions-container vertical-flex"
        )

    pass
