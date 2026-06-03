from dash import html, dcc


navbar = html.Div([
    html.Div("Purchasing Dashboard", className="navbar-title"),
    html.Div([
        dcc.Link("Home", href="/", className="nav-link"),
        dcc.Link("Vendor Snapshot", href="/vendorSnapshot", className="nav-link"),
        dcc.Link("Item History and Forecasting", href="/byItem", className="nav-link"),
        dcc.Link("Retail Build-Out", href="/retailBuildout", className="nav-link")
    ]),
    dcc.Loading(id="dummy-loading", type="circle")
    ], className="navbar-container"
)
"""
Top navigation bar.
"""
