from dash import html, dcc

filter_sidebar = html.Div([
    html.Label("Filter by Vendor(s)", className="sidebar-label sidebar-label-margin"),
    dcc.Dropdown(id='vendor-id-filter', placeholder="Select Vendor ID", multi=True, searchable=True),

    html.Form(
            children=[
                html.Label(children="Search", htmlFor="vendor-snapshot-table-search", 
                            className="sidebar-label sidebar-form-label"),
                dcc.Input(
                    id="vendor-snapshot-table-search",
                    type="search",
                    placeholder="Enter Search Term",
                    debounce=True, # don't search until the element loses focus
                    className="sidebar-search"
                ),
            ],
        method="dialog",
        className="sidebar-form"
    ),
], className='sidebar-container')
