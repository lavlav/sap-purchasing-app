import dash
from dash import html

from purchasing_dashboard.layout.product_buildout.main_content import retail_buildout_main_content

dash.register_page(__name__, path="/retailBuildout", name="Retail Build-Out")

layout=html.Div([
    retail_buildout_main_content
])