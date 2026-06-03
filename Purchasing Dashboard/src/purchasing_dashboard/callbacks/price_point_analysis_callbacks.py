from dash import callback, Input, Output, no_update
import pandas
import numpy as np
import plotly.graph_objects as pgo

from purchasing_dashboard.layout.aio.coefficients import Coefficients
from purchasing_dashboard.layout.aio.price_point_panel import PricePointPanel
from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.layout.common.store import ALL_ORDERS_DATA_STORE_ID

class NotEnoughDataError(Exception):

    def __init__(self, message, n_points):
        super().__init__(message)
        self.message = message
        self.n_points = n_points

def get_price_points_for_items(orders_data, item_codes):
    """
    Return a DataFrame with OrderDate, Price and QuantityOrdered columns for items
    among the given orders_data.
    """
    if not orders_data or not item_codes:
        return pandas.DataFrame(columns=["OrderDate", "QuantityOrdered", "Price"])

    df = pandas.DataFrame(orders_data)
    filtered = df[df['ItemCode'].isin(item_codes)].drop_duplicates(subset=['QuantityOrdered', 'Price'])
    filtered["TotalPrice"] = filtered["QuantityOrdered"] * filtered["Price"]
    n_points = len(filtered)
    if n_points < 2:
        raise NotEnoughDataError(f"Not enough price data points to compute price points: {n_points}", n_points)
    price_mean = filtered["TotalPrice"].mean()
    price_std_dev = filtered["TotalPrice"].std()
    filtered["Outlier"] = (np.abs(filtered["TotalPrice"] - price_mean) > 2 * price_std_dev)
    return filtered[["OrderDate", "QuantityOrdered", "Price", "TotalPrice", "Outlier"]]

@callback(
    Output(PricePointPanel.ids.plot("price-point-analysis"), "figure"),
    Output(PricePointPanel.ids.coefficient("price-point-analysis", "Quantity"), "data"),
    Output(PricePointPanel.ids.info_message("price-point-analysis"), "children"),
    Input(ALL_ORDERS_DATA_STORE_ID, "data"),
    Input("item-code-filter", "value"),
    Input(PricePointPanel.ids.input("price-point-analysis", "Quantity"), "value"),
    # prevent_initial_call=True
)
def update_coefficients(orders_data, item_codes, user_quantity):
    """
    Update the price point coefficients and info message based on the orders data and selected item codes.
    """
    if not item_codes:
        return no_update, no_update, None # Will be hidden by the tab content callback
    if not orders_data:
        return no_update, Coefficients.DEFAULT, f"No recent orders data available for {item_codes}."
    # if type(item_codes) is list and len(item_codes) > 1:
    #     return no_update, Coefficients.DEFAULT, f"Can't analyze price points for multiple items."
    try:
        price_points = get_price_points_for_items(orders_data, item_codes)
    except NotEnoughDataError as e:
        logger.error(f"Error processing orders data: {e}")
        return no_update, Coefficients.DEFAULT, e.message
    user_quantity = user_quantity if user_quantity is not None else 1

    regular_price_points = price_points[price_points["Outlier"] == False]
    outlier_price_points = price_points[price_points["Outlier"]]
    regular_quantities = regular_price_points["QuantityOrdered"]
    regular_prices = regular_price_points["TotalPrice"]
    outlier_prices = outlier_price_points["TotalPrice"]
    outlier_quantities = outlier_price_points["QuantityOrdered"]

    slope, intercept = np.polyfit(regular_quantities, regular_prices, 1)
    logger.debug(f"Computed coefficients: slope={slope}, intercept={intercept}")
    fig = pgo.Figure()
    hovertemplate = "<b>Order Date: %{customdata[0]}</b><br>Quantity: %{x}<br>Unit Price: %{customdata[1]} <br>Order Price: %{y} <br><extra></extra>"
    price_point_scatter = pgo.Scatter(
        x=regular_quantities, 
        y=regular_prices, 
        mode='markers',
        marker=dict(color='blue', size=8),
        hovertemplate=hovertemplate,
        customdata=price_points[["OrderDate", "Price"]],
        name='Price Points'
        )
    outlier_scatter = pgo.Scatter(
        x=outlier_quantities, 
        y=outlier_prices, 
        mode='markers',
        hovertemplate=hovertemplate,
        customdata=outlier_price_points[["OrderDate", "Price"]],
        marker=dict(color='rgba(255, 0, 0, 0.5)', symbol='x', size=10),
        name='Outliers'
    )
    # Extrapolated values outside the range of the data are dashed
    line_of_best_fit_plot_outer = pgo.layout.Shape(
        type="line",
        xref="x",
        yref="y",
        x0=0,
        y0=intercept,
        x1=regular_quantities.max() * 1.5,
        y1=slope * regular_quantities.max() * 1.5 + intercept,
        line=dict(color='red', dash='dot', width=1),
    )
    # Interpolated values inside the range of the data are solid
    line_of_best_fit_plot_inner = pgo.layout.Shape(
        type="line",
        xref="x",
        yref="y",
        x0=regular_quantities.min(),
        y0=slope * regular_quantities.min() + intercept,
        x1=regular_quantities.max(),
        y1=slope * regular_quantities.max() + intercept,
        line=dict(color='red'),
    )
    user_selection_plot = pgo.Scatter(
        x=[user_quantity],
        y=[slope * user_quantity + intercept],
        mode='markers',
        marker=dict(
            symbol='star',
            color='orange', 
            size=10
            ),
        name='Your Selection'
    )
    fig.add_trace(price_point_scatter)
    fig.add_trace(outlier_scatter)
    fig.add_shape(line_of_best_fit_plot_outer)
    fig.add_shape(line_of_best_fit_plot_inner)
    fig.add_trace(user_selection_plot)
    fig.update_layout(
        title="Price vs Quantity Ordered",
        xaxis_title="Quantity Ordered",
        yaxis_title="Price",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(color='black', linecolor='black', gridcolor='darkgrey', rangemode='tozero'),
        yaxis=dict(color='black', linecolor='black', gridcolor='darkgrey', rangemode='tozero'),
    )
    return fig, Coefficients(slope=slope, intercept=intercept), None