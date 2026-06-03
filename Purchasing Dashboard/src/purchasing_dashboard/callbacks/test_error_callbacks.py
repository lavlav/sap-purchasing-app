from dash import Input, Output, callback, no_update


@callback(
    Output("url", "id"),
    Input("url", "pathname"),
)
def test_global_error_handling(pathname: str):
    """
    A dummy callback to test error handling.
    """
    if pathname == "/cause-error":
        raise Exception("This is a test error triggered by navigating to /cause-error.")
    if pathname == "/cause-long-error":
        raise Exception((("This is a test error triggered by navigating to /cause-long-error " + 
                        "to see how really long exceptions are visualized.\n") * 50))
    return no_update