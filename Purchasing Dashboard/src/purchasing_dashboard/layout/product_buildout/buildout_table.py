from dash import dcc, html
from dash.dash_table import DataTable

from purchasing_dashboard.layout.common.inline_styles import GRAY_OUT_EXCLUDED_STYLE_DATA_CONDITIONAL, STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL
from purchasing_dashboard.utils.placeholder_data import generate_placeholder_table_data

_COLUMNS = [
    {"name": "Include/Exclude", "id": "Include", "presentation": "dropdown", "editable": True},
    {"name": "Item Code", "id": "ItemCode", "type": "text"},
    {"name": "Item Name", "id": "ItemName", "type": "text"},
    {"name": "Ea/Case", "id": "EachesPerCase", "type": "text"},
    {"name": "Eaches In Stock", "id": "EachesInStock", "type": "numeric"},
    {"name": "Days On Hand", "id": "DaysOnHand", "type": "numeric"},
]

# Add dropdown options for the 'Include' column
_DROPDOWN = {
    'Include': {
        'options': [
            {'label': 'Include', 'value': 'true'},
            {'label': 'Exclude', 'value': 'false'}
        ]
    }
}

_PLACEHOLDER = generate_placeholder_table_data([col["id"] for col in _COLUMNS])

for record in _PLACEHOLDER:
    if record['Include'] and record['Include'] not in ['true', 'false']:
        record['Include'] = 'true'

_STYLE_DATA_CONDITIONAL = STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL + GRAY_OUT_EXCLUDED_STYLE_DATA_CONDITIONAL

class BuildoutTable(html.Div):
    """A DataTable for displaying product buildout information."""

    class ids:
        @staticmethod
        def table(aio_id: str) -> dict:
            return {
                "component": "BuildoutTable",
                "subcomponent": "table",
                "aio_id": aio_id
            }
        
        @staticmethod
        def loading(aio_id: str) -> dict:
            return {
                "component": "BuildoutTable",
                "subcomponent": "loading",
                "aio_id": aio_id
            }

    def __init__(self, aio_id: str):
        # TODO #41: consider migrating to Dash AG Grid, as it's more flexible for this use case
        table = DataTable(
            id=BuildoutTable.ids.table(aio_id),
            columns=_COLUMNS,
            data=_PLACEHOLDER,
            page_size=15,
            sort_action="native",
            row_deletable=False,
            editable=False,
            style_data_conditional=_STYLE_DATA_CONDITIONAL,
            dropdown=_DROPDOWN,
        )
        children = [
            dcc.Loading(
                id=BuildoutTable.ids.loading(aio_id),
                children=[
                    table
                ]
            )
        ]
        super().__init__(
            children=children,
            className="striped-table buildout-table-container"
        )