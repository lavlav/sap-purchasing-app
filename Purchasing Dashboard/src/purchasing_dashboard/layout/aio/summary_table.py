import calendar
from purchasing_dashboard.layout.common.inline_styles import STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL
from purchasing_dashboard.utils.placeholder_data import generate_placeholder_table_data


from dash import MATCH, Input, Output, callback, dash_table, html
from dash.dash_table.Format import Format

# Define the columns for the historic usage table
CALENDAR_MONTHS = [calendar.month_abbr[i] for i in range(1, 13)]
HISTORIC_USAGE_TABLE_COLUMNS = [
    "Date", "Year"] + [f"Q{i}" for i in range(1, 5)] + CALENDAR_MONTHS + ["Units Sold"]
HISTORIC_USAGE_TABLE_COLUMN_IDS = [col.replace(
    " ", "") for col in HISTORIC_USAGE_TABLE_COLUMNS]
QUARTERS = [f"Q{i}" for i in range(1, 5)]
HISTORIC_USAGE_TABLE_COLUMN_HIDE_MASK = {
    "day": list(set(HISTORIC_USAGE_TABLE_COLUMN_IDS) - set(["Date", "UnitsSold"])),
    "week": list(set(HISTORIC_USAGE_TABLE_COLUMN_IDS) - set(["Date", "UnitsSold"])),
    "month": list(set(HISTORIC_USAGE_TABLE_COLUMN_IDS) - set(CALENDAR_MONTHS + ["Year"])),
    "quarter": list(set(HISTORIC_USAGE_TABLE_COLUMN_IDS) - set(QUARTERS + ["Year"])),
    "year": list(set(HISTORIC_USAGE_TABLE_COLUMN_IDS) - set(["Year", "UnitsSold"])),
}


class SummaryTableAIO(html.Div):
    """
    A summary table that displays "summary" (aggregated) numerical data according to the chosen time bucket.
    """
    class ids:
        @staticmethod
        def table(aio_id):
            return {"component": "SummaryTableAIO", "subcomponent": "table", "aio_id": aio_id}

        @staticmethod
        def container(aio_id):
            return {"component": "SummaryTableAIO", "subcomponent": "container", "aio_id": aio_id}

        @staticmethod
        def info_message(aio_id):
            return {"component": "SummaryTableAIO", "subcomponent": "info-message", "aio_id": aio_id}

    ids = ids

    def __init__(self, aio_id):
        super().__init__(id=self.ids.container(aio_id), children=[
            dash_table.DataTable(
                id=self.ids.table(aio_id),
                columns=[
                    {
                        "name": HISTORIC_USAGE_TABLE_COLUMNS[i],
                        "id": HISTORIC_USAGE_TABLE_COLUMN_IDS[i],
                        "type": "numeric" if not HISTORIC_USAGE_TABLE_COLUMN_IDS[i] in ["Year", "Date"] else "datetime",
                        "format": Format().group(True)  # add commas for numeric values
                    } for i in range(len(HISTORIC_USAGE_TABLE_COLUMNS))],
                hidden_columns=HISTORIC_USAGE_TABLE_COLUMN_HIDE_MASK["month"],
                data=generate_placeholder_table_data(
                    HISTORIC_USAGE_TABLE_COLUMNS),
                page_size=10,
                # sort_action='native',
                # sort_mode='multi',
                persistence=False,  # True,
                persistence_type='session',
                persisted_props=['data', 'columns.name', 'filter_query', 'hidden_columns',
                                 'page_current', 'selected_columns', 'selected_rows', 'sort_by'],
                style_data_conditional=STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL
            ),
            html.Label(
                id=self.ids.info_message(aio_id),
                children=[],
                className="info-text"
            )
        ], className="summary-table-container striped-table")

    @callback(
        Output(ids.table(MATCH), "hidden_columns"),
        Input("time-interval-picker", "value")
    )
    def update_hidden_columns(selected_time_interval: str):
        return HISTORIC_USAGE_TABLE_COLUMN_HIDE_MASK[selected_time_interval]
