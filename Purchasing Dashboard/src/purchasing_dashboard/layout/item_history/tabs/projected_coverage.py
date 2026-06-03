from dash.dash_table.Format import Format, Scheme
import logging

from purchasing_dashboard.layout.aio.groupable_projection_panel import GroupableProjectionPanelAIO

from purchasing_dashboard.layout.aio.tab_content_container import TabContentContainerAIO
from purchasing_dashboard.utils.logging import logger

PROJECTED_COVERAGE_TABLE_COLUMN_NAMES = ["Item Code", "Time", "Usage", "Incoming", "Units Available"]

PROJECTED_COVERAGE_TABLE_COLUMNS = [{
    "name": name,
    "id": name,
    "type": "numeric" if name in ["Usage", "Incoming", "Units Available"] else "text",
    "format": Format(scheme=Scheme.decimal_integer).group(True) if name in ["Units Available", "Usage", "Incoming"] else None
} for name in PROJECTED_COVERAGE_TABLE_COLUMN_NAMES
]

PROJECTED_COVERAGE_PANEL = GroupableProjectionPanelAIO(
    PROJECTED_COVERAGE_TABLE_COLUMNS, "Item Code", "Time", "Units Available", 
    aio_id="projected-coverage", 
    dependent_ids = [TabContentContainerAIO.ids.loading_wrapper("projected-coverage-container")]
    )

