from dash import html

from purchasing_dashboard.layout.aio.coefficients import format_markdown_template
from purchasing_dashboard.layout.aio.coefficients import Coefficients
from purchasing_dashboard.layout.aio.price_point_panel import PricePointPanel

PRICE_POINT_ANALYSIS_CONTENT = html.Div([
    PricePointPanel(
        aio_id="price-point-analysis",
        equation_latex=format_markdown_template(Coefficients.DEFAULT),
        input_variables=["Quantity"],
        output_variable="Price",
    )
])
