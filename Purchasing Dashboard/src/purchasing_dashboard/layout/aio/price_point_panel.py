from dash import MATCH, callback, html, dcc, Input, Output, State, no_update
import plotly.graph_objects as pgo

from purchasing_dashboard.layout.aio.coefficients import Coefficients
from purchasing_dashboard.layout.aio.coefficients import format_markdown_template
from purchasing_dashboard.utils.classnames import toggle_hidden_class
from purchasing_dashboard.utils.icons import Icons
from purchasing_dashboard.utils.logging import logger


class PricePointPanel(html.Div):
    """
    A Dash component that represents a Markdown LaTeX-formatted linear equation, 
    with input controls underneath to "plug-in" values.

    The Markdown is expected to be of the form :

    `<coefficient1>\\cdot\\text{var1} + <coefficient2>\cdot\\text{var2} + ... = <output_variable>`

    Deviations may affect how the coefficients are dynamically updated.
    """

    class ids:
        @staticmethod
        def plot(aio_id: str) -> dict:
            return {
                "component": "PricePointPanel",
                "subcomponent": "plot",
                "aio_id": aio_id
            }

        @staticmethod
        def markdown(aio_id: str) -> dict:
            return {
                "component": "PricePointPanel",
                "subcomponent": "markdown",
                "aio_id": aio_id
            }

        @staticmethod
        def coefficient(aio_id: str, variable_name: str = "") -> dict:
            if not variable_name:
                return {
                    "component": "PricePointPanel",
                    "subcomponent": "coefficient",
                    "aio_id": aio_id
                }
            else:
                return {
                    "component": "PricePointPanel",
                    "subcomponent": "coefficient",
                    "variable_name": variable_name,
                    "aio_id": aio_id
                }

        @staticmethod
        def input(aio_id: str, variable_name: str = "") -> dict:
            if not variable_name:
                return {
                    "component": "PricePointPanel",
                    "subcomponent": "input",
                    "aio_id": aio_id
                }
            else:
                return {
                    "component": "PricePointPanel",
                    "subcomponent": "input",
                    "variable_name": variable_name,
                    "aio_id": aio_id
                }

        @staticmethod
        def output(aio_id: str) -> dict:
            return {
                "component": "PricePointPanel",
                "subcomponent": "output",
                "aio_id": aio_id
            }

        @staticmethod
        def info_message(aio_id: str) -> dict:
            return {
                "component": "PricePointPanel",
                "subcomponent": "info_message",
                "aio_id": aio_id
            }
        
        @staticmethod
        def container(aio_id: str) -> dict:
            return {
                "component": "PricePointPanel",
                "subcomponent": "container",
                "aio_id": aio_id
            }

    ids = ids

    def __init__(self,
                 aio_id: str,
                 equation_latex: str,
                 input_variables: list[str],
                 output_variable: str = ""):
        graph = dcc.Graph(
            id=self.ids.plot(aio_id),
            figure=pgo.Figure(),
        )
        inputs = html.Div([
            html.Div([
                dcc.Store(id=self.ids.coefficient(aio_id, var),
                          data=Coefficients(slope="m", intercept="b")),
                dcc.Input(id=self.ids.input(aio_id, var),
                          className="medium-input", type="number", value=1),
                html.Label(f"({var})"),
            ], className="pluggable-equation-input horizontal-flex") for var in input_variables
        ] + [
            html.Img(src=Icons.RIGHT_ARROW.path, className="icon"),
            html.Label(id=self.ids.output(aio_id)),
            f"({output_variable})"
        ],
            className="pluggable-equation-inputs")
        markdown = dcc.Markdown(
            id=self.ids.markdown(aio_id),
            className="pluggable-equation-markdown",
            children=equation_latex,
            mathjax=True
        )
        info_message = html.Label(
            id=self.ids.info_message(aio_id),
            className="info-text warning"
        )
        super().__init__(children=[
            html.Div(
                id=self.ids.container(aio_id),
                children=[
                    graph,
                    html.Div([
                        markdown,
                        inputs
                    ], className="vertical-flex")
                ], className="horizontal-flex pluggable-equation-container"),
            info_message
        ], className="vertical-flex centered-flex-container")

    @callback(
        Output(ids.output("price-point-analysis"), "children"),
        Input(ids.input("price-point-analysis", "Quantity"), "value"),
        State(ids.coefficient("price-point-analysis", "Quantity"), "data"),
        prevent_initial_call=True
    )
    def compute_output(inputs, coefficients):
        """
        Compute the output of the equation based on the inputs and coefficients.
        """
        logger.debug(
            f"Computing output with inputs={inputs}, coefficients={coefficients}")
        if coefficients == Coefficients.DEFAULT:
            return "N/A"
        return coefficients["slope"] * inputs + coefficients["intercept"]

    @callback(
        Output(ids.markdown("price-point-analysis"), "children"),
        Input(ids.coefficient("price-point-analysis", "Quantity"), "data"),
        prevent_initial_call=True
    )
    def update_markdown(coefficients):
        """Update the markdown text with the current coefficients."""
        if not coefficients or len(coefficients) < 2:
            logger.warning("Insufficient coefficients to update markdown.")
            return no_update
        slope, intercept = coefficients
        logger.debug(
            f"Updating markdown with slope={slope}, intercept={intercept}")
        return format_markdown_template(coefficients)

    @callback(
        Output(ids.container("price-point-analysis"), "className"),
        State(ids.container("price-point-analysis"), "className"),
        Input(ids.info_message("price-point-analysis"), "children"),
    )
    def hide_container(old_classname, info_message):
        """Hide the container if the info message is not empty."""
        show = not info_message
        return toggle_hidden_class(old_classname, not show)
