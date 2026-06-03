
from dash import html, dcc

from purchasing_dashboard.layout.aio.item_subselector import ItemSubselectorAIO

# TODO #74: restyle this
# TODO #17: move into an AIO
def info_box(name, content_id, content_placeholder):
    return html.Div([
        name,
        html.Label(content_placeholder, id=content_id, className="info-box-content"),
        dcc.Tooltip(id=f"{content_id}-tooltip",
            children=None)
    ], className="info-box")

item_order_summary_header = html.Div([
    ItemSubselectorAIO(aio_id="item-subselector"),
    html.Div([
        info_box("Avg. Monthly Usage: ", "avg-monthly-usage-label", "..."),
        info_box("Units in Stock: ", "units-in-stock-label", "..."),
        info_box("Days on Hand: ", "days-on-hand-label", "..."),
        info_box("Most recent price per unit: ", "most-recent-price-label", "..."),
    ], className="info-box-row"),
])
