from dash import html, dcc
import plotly.express as px
import pandas

ITEM_HISTORY_FIGURE = px.line(
    data_frame=pandas.DataFrame(
        columns=["Time", "Units"]),
    x="Time",
    y="Units"
)

HISTORIC_DEMAND_SUMMARY_PLOT_CONTENT = dcc.Graph(
    id="historic-demand-plot",
    figure=ITEM_HISTORY_FIGURE,
    className="historic-demand-plot item-history-graph"
)
