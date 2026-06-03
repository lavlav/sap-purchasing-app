from frozendict import frozendict
import pandas as pd
import plotly.graph_objects as pgo
import numpy as np
from dash import MATCH, Input, Output, Patch, State, callback, dcc, html, no_update
from dash.dash_table import DataTable
import uuid
import logging

from pydantic import BaseModel, ConfigDict, field_validator

from purchasing_dashboard.layout.common.store import STORE_TO_DEPENDENTS
from purchasing_dashboard.utils.logging import logger


class GroupableProjectionPanelAIO(html.Div):
    """
    AIO component with a bar chart and a data table that can be grouped by a specified column.
    The bar chart displays data grouped by the specified column, and the data table shows detailed information.
    Intended for use "projecting" future values of a time series, such as inventory levels.
    """

    class ids:
        @staticmethod
        def bar_chart(aio_id): return {
            "component": "GroupableProjectionPanelAIO",
            "subcomponent": "bar-chart",
            "aio_id": aio_id
        }

        @staticmethod
        def table(aio_id): return {
            "component": "GroupableProjectionPanelAIO",
            "subcomponent": "table",
            "aio_id": aio_id
        }

        @staticmethod
        def group_checkbox(aio_id): return {
            "component": "GroupableProjectionPanelAIO",
            "subcomponent": "group-checkbox",
            "aio_id": aio_id
        }

        @staticmethod
        def store(aio_id): return {
            "component": "GroupableProjectionPanelAIO",
            "subcomponent": "store",
            "aio_id": aio_id
        }

    # make ids a public class
    ids = ids

    def __init__(
        self,
        columns: list[str] | list[dict],
        group_column,
        x_column,
        y_column,
        dependent_ids=[],
        bar_chart_props=None,
        group_checkbox_props=None,
        datatable_props=None,
        aio_id=None
    ):
        """
        AIO component with a checkbox and a bar chart. The checkbox can be clicked
        to group the bar chart if multiple items are being visualized.

        Arguments:
            columns (list[str]): List of column names in the data to be displayed.
            This is the same structure as Dash [DataTable](https://dash.plotly.com/datatable/reference)'s `columns` prop.
            group_column (str): The name of the column to group data by.
            x_column (str): The name of the column on the x-axis (typically a date).
            y_column (str): The name of the column on the y-axis (typically a numeric value).
            bar_chart_props (dict): Properties for the bar chart, such as layout and style.
            group_checkbox_props (dict): Properties for the group checkbox, such as options and value.
            datatable_props (dict): Properties for the data table, such as columns and styles.
            aio_id (str): Unique identifier for the AIO component.
        """  
        # TODO #74: include args and components in the above docstring
        logger.debug(f"Instantiating GroupableProjectionPanelAIO with {len(columns)} columns. ")
        for id in dependent_ids:
            this_id = frozendict(GroupableProjectionPanelAIO.ids.store(aio_id))
            mapping = STORE_TO_DEPENDENTS.get(this_id, set())
            mapping.add(frozendict(id))
            STORE_TO_DEPENDENTS[this_id] = mapping
            logger.debug("Mapping data dependency")


        if isinstance(columns[0], str):
            _columns = columns
            datatable_columns = [{"name": col, "id": col} for col in columns]
        elif isinstance(columns[0], dict) and all("name" in col for col in columns):
            _columns = [col["name"] for col in columns]
            datatable_columns = columns
        else:
            raise ValueError("columns must be a list of strings or a list of dicts with 'name' keys")
        
        for col in [group_column, x_column, y_column]:
            if (not col in _columns):
                raise ValueError(f"Column {col} not found in {_columns}")

        # set defaults
        if aio_id is None:
            aio_id = str(uuid.uuid4())
        bar_chart_props = bar_chart_props or {}
        # "figure": px.bar(pd.DataFrame(columns=columns),x=x_column, y=y_column, title=title)}
        group_checkbox_props = group_checkbox_props or {
            "options": [{
                "label": f"Group {group_column}",
                "value": "grouped"
            }],
            "value": []
        }
        datatable_props = datatable_props or {}

        children = [
            dcc.Store(
                id=self.ids.store(aio_id),
                data={
                    "group_column": group_column,
                    "x_column": x_column,
                    "y_column": y_column
                }
            ),
            html.Div([
                html.Div([
                    DataTable(
                        id=self.ids.table(aio_id),
                        page_size=10,
                        columns=datatable_columns,
                        **datatable_props
                    )],
                    className="projected-coverage-aio-table-container"),

                html.Div([
                    dcc.Graph(
                        id=self.ids.bar_chart(aio_id),
                        figure=pgo.Figure(),
                        **bar_chart_props
                    )],
                    className="projected-coverage-aio-graph-container"),
            ], className="projected-coverage-aio-container"),
            dcc.Checklist(id=self.ids.group_checkbox(aio_id),
                          **group_checkbox_props
                          ),

        ]
        super().__init__(children=children)

    @callback(
        Output(ids.bar_chart(MATCH), "figure"),
        Output(ids.table(MATCH), "data"),
        Output(ids.table(MATCH), "hidden_columns"),
        State(ids.bar_chart(MATCH), "figure"),
        Input(ids.store(MATCH), "data"),
        Input(ids.group_checkbox(MATCH), "value"),
        prevent_initial_call=True
    )
    def plot_bar_chart_and_fill_data_table(figure_raw: dict, data: dict, group_checkbox: list[str]):
        """
        Plot a bar chart and fill a data table based on the provided data and checkbox values.

        Args:
            figure_raw (dict): The raw figure data for the bar chart.
            group_checkbox (list[str]): Checkbox value indicating whether to group the chart.
            data (dict): The data to be visualized and displayed in the data table and chart.

        Returns:
            tuple:
            - figure (pgo.Figure): The updated bar chart figure.
            - data (list[dict]): Data for the table.
            - hidden_columns (list[str]): Columns to hide in the table depending on the group checkbox.

        Raises:
            ValueError: If required columns are missing from the data.
        """
        if not data:
            logger.debug("No data to display in projected coverage.")
            return no_update, no_update, no_update
        projection_data = ProjectionData(**data)
        group_column = projection_data.group_column
        x_column = projection_data.x_column
        y_column = projection_data.y_column
        logger.debug(f"group_column: {group_column}")
        should_group_display = "grouped" in group_checkbox
        # pull the dataframe
        if should_group_display:
            df = projection_data.grouped_dataframe
        else:
            df = projection_data.individual_dataframe
        if df.empty:
            logger.warning("No data for projected coverage table")
            return no_update, no_update, no_update
        group_column_values = df[group_column].nunique()
        if (group_column_values == 0):
            logger.error(
                f"No {group_column} values found in the provided data.")
            return no_update, no_update, no_update
        elif (group_column_values == 1 and should_group_display):
            logger.warning(
                f"Only found {group_column_values} for {group_column}. Can't group.")
        dashed_line_level = projection_data.dashed_line_threshold
        figure = pgo.Figure(figure_raw)
        figure.data = []
        # Get unique items
        items_unique = df[group_column].unique()

        # Create hue variations by ItemCode (used as intensity component)
        intensities = np.linspace(60, 160, len(items_unique), dtype=int)
        intensity_map = dict(zip(items_unique, intensities))
        intensity_map["All Items"] = 0  # default for aggregated view

        # Function to compute color for each bar
        def bar_color(item, y_val):
            g = intensity_map[item]
            y_val = y_val or 0  # Ensure y_val is not NaN
            if y_val >= 0:
                return f'rgba({g},255,{g},1.0)'  # greenish
            else:
                return f'rgba(255,{g},{g},1.0)'  # reddish

        # Build bar traces
        traces = []
        for item in items_unique:
            if should_group_display:
                subset = df
            else:
                subset = df[df[group_column] == item].sort_values(by=x_column)
            colors = [bar_color(item, y) for y in subset[y_column]]

            traces.append(pgo.Bar(
                x=subset[x_column],
                y=subset[y_column],
                name=item,
                marker=dict(color=colors),
                hoverinfo='x+y+name'
            ))
        figure.add_traces(traces)
        # Set the figure layout
        figure.update_layout(
            shapes=[
                # dashed line
                dict(
                    type="line",
                    xref="paper",  # full width of x-axis
                    x0=0,
                    x1=1,
                    yref="y",
                    y0=dashed_line_level,
                    y1=dashed_line_level,
                    line=dict(
                        color="black",
                        width=2,
                        dash="dash"
                    )
                )
            ],
            barmode="group",
            title=f"{", ".join(items_unique)} {y_column} by {x_column}",
            xaxis_title=x_column,
            yaxis_title=y_column,
            xaxis_fixedrange=True,
            yaxis_fixedrange=True
        )
        hidden_columns = [group_column] if should_group_display else []
        return figure, df.to_dict("records"), hidden_columns

class ProjectionData(BaseModel):
    """
    Data model for projected coverage data, including individual and grouped dataframes,
    used to configure GroupableProjectionPanelAIO.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    individual_dataframe: pd.DataFrame | dict
    grouped_dataframe: pd.DataFrame | dict
    dashed_line_threshold: float
    group_column: str
    x_column: str
    y_column: str
    display_individually: bool = False

    @field_validator("dashed_line_threshold")
    def validate_dashed_line(cls, value):
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError("dashed_line must be a number")
        if value is None:
            return 0.0
        return value

    @field_validator("individual_dataframe", "grouped_dataframe")
    def validate_dataframe(cls, value):
        if isinstance(value, pd.DataFrame):
            return value
        elif isinstance(value, dict):
            return pd.DataFrame.from_dict(value)
        else:
            raise ValueError(f"Expected {value} to be a pandas DataFrame or a dictionary")