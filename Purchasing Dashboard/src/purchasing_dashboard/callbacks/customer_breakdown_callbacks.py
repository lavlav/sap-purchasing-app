from dash import callback, Output, Input, State, ctx, no_update
import plotly.graph_objects as pgo
from plotly.subplots import make_subplots
from scipy.__config__ import show

from purchasing_dashboard.layout.common.store import CUSTOMER_BREAKDOWN_STORE_ID, get_dependent_outputs_for_store
from purchasing_dashboard.layout.item_history.tabs.customer_breakdown import n_visible_categories
from purchasing_dashboard.utils.api import api
from purchasing_dashboard.utils.logging import logger
from dashboard_common.model.customer_distribution import CustomerDistribution

def blank_figure() -> pgo.Figure:
    """
    Returns a blank Plotly figure with no data.
    This is used as a placeholder when no customer breakdown data is available.
    """
    return pgo.Figure(
        layout=pgo.Layout(
            title="No Data Available",
            xaxis_title="Customer Type",
            yaxis_title="Value",
            showlegend=False
        )
    )

@callback(
    Output(CUSTOMER_BREAKDOWN_STORE_ID, "data"),
    Input("item-code-filter", "value"),
    background=True,
    running=get_dependent_outputs_for_store(CUSTOMER_BREAKDOWN_STORE_ID),
    prevent_initial_call=True,
)
def update_customer_breakdown_store(item_codes):
    """
    Update the customer breakdown store with the item code and order history data.
    This function is triggered by changes in the item code filter or URL pathname.
    """
    if not item_codes or len(item_codes) == 0:
        logger.warning("No item codes provided for customer breakdown store update.")
        return no_update
    # Placeholder for actual data retrieval logic
    if ctx.triggered_id == "item-code-filter":
        logger.info(f"Updating customer breakdown store for item codes: {item_codes}")
    elif ctx.triggered_id == "url":
        #if pathname != "byItem":
        #    return no_update
        logger.info(f"Updating customer breakdown store after entering item history page.")
    else:
        logger.warning(f"Unexpected trigger: {ctx.triggered_id}")
    customer_breakdown_json = api.fetch_customer_breakdown(item_codes)
    return customer_breakdown_json


@callback(
    Output("customer-breakdown-bar-chart", "figure"),
    Input(CUSTOMER_BREAKDOWN_STORE_ID, "data"),
    Input("customer-breakdown-sort-toggle", "value"),
    State("customer-breakdown-bar-chart", "figure"),
)
def update_customer_breakdown_bar_chart(customer_breakdown_json, sort_by, current_figure):
    """
    Update the customer breakdown bar chart based on the customer distribution data and sort preference.
    """
    if not customer_breakdown_json or not customer_breakdown_json["customer_data"]:
        logger.warning("No customer breakdown data available.")
        return blank_figure()
    sort_by = sort_by[:1].upper() + sort_by[1:]  # Capitalize first letter to match the columns
    logger.info(f"Updating customer breakdown bar chart with sort by: {sort_by}")
    customer_distribution = CustomerDistribution.model_validate(customer_breakdown_json)
    df = customer_distribution.customer_data.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
    # Create a bar chart figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        pgo.Bar(
            x=df["AccountType"],
            y=df["Units"],
            name="Units",
            marker_color="steelblue",
            offsetgroup=1,  # group ID for bar positioning
            text=df["Units"].apply(lambda x: f"{x:,} Units"),              # show values
            textposition="outside",         # display above bars
            hovertemplate="%{x}: %{y:,} Units"  # format hover text
        ),
        secondary_y=False
    )

    # Sales bars (secondary y-axis)
    fig.add_trace(
        pgo.Bar(
            x=df["AccountType"],
            y=df["Sales"],
            name="Sales",
            marker_color="orange",
            offsetgroup=2,  # group ID for bar positioning
            text=df["Sales"].apply(lambda x: f"${x:,.2f}"),              # show values
            textposition="outside",         # display above bars
            hovertemplate="%{x}: %{y:,.2f} USD"  # format hover text
        ),
        secondary_y=True
    )

    # Update layout
    fig.update_layout(
        barmode="group",  # groups them side by side
        margin=dict(t=40, r=0, b=0, l=0),  # reduce top margin, reclaim space
        xaxis=dict(
            title="Customer Type",
            range=[-0.5, n_visible_categories - 0.5],            # show only N categories at once
            fixedrange=False,           # allow panning
            rangebreaks=[],             # no skipped categories
            constrain="domain",         # keep axis within domain
            minallowed=-0.5,            # leftmost bar
            maxallowed=len(df) - 0.5   # rightmost bar
        ),
        xaxis_title="Customer Type",
        legend_title="Metric",
        legend = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.5
        ),
        dragmode="pan",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )

    # Set y-axes titles
    fig.update_yaxes(title_text="Units", secondary_y=False, fixedrange=True)
    fig.update_yaxes(title_text="Sales", secondary_y=True, fixedrange=True)

    return fig
