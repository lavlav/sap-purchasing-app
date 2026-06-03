

import diskcache
from purchasing_dashboard.layout.aio import item_code_selector
from purchasing_dashboard.layout.common.error_modal import error_modal
from purchasing_dashboard.layout.common.store import common_store
from purchasing_dashboard.layout.item_history.sidebar.sidebar import item_code_selector
from purchasing_dashboard.layout.common.navbar import navbar
import dash
from dash import Dash, DiskcacheManager, html
import dash_auth
import os
import base64

from purchasing_dashboard.utils.error_handler import handle_callback_error
from purchasing_dashboard.utils.logging import logger
from purchasing_dashboard.utils.environment_variables import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME, BASIC_AUTH_USERNAME, DEBUG_ENABLED, LOG_LEVEL

# TODO #74: use a redis manager instead of diskcache in beta and prod
cache = diskcache.Cache("./.cache")
background_callback_manager = DiskcacheManager(cache)

# TODO #74: remove this when implementing proper Kerberos/LDAP/OIDC authentication
# HTTP Basic Auth for development purposes
DEVELOPER_AUTH = {
    BASIC_AUTH_USERNAME: BASIC_AUTH_PASSWORD
}

app = Dash(__name__, 
           use_pages=True, 
           show_undo_redo=DEBUG_ENABLED,
           background_callback_manager=background_callback_manager,
           # suppress_callback_exceptions=not DEBUG_ENABLED,
           suppress_callback_exceptions=True, # always True to avoid issues with pages
           on_error=handle_callback_error)
auth = dash_auth.BasicAuth(
    app,
    DEVELOPER_AUTH,
    secret_key=base64.b64encode(os.urandom(30)).decode('utf-8')
)


app.layout = html.Div([
    error_modal,
    navbar,
    dash.page_container,
    common_store,
])

# Special: add all the pages in the page registry to the app's validation layout
# This prevents Dash from throwing errors about callbacks referencing components
# that are not in the initial layout. See https://dash.plotly.com/urls for details.
# This is only necessary in debug mode, as suppress_callback_exceptions is set to True 
# in production mode.
# TODO #74: investigate if this is still necessary with suppress_callback_exceptions=True
if DEBUG_ENABLED:
    app.validation_layout = html.Div([
        app.layout,
        *[page["layout"] for page in dash.page_registry.values()],
        # Special:
        # For some reason, this does not get registered before the callback that uses it is fired,
        # even though it should be in the item history page's layout as above.
        # This is probably a bug in Dash, but for now we can just add it here
        item_code_selector
    ])

# Register callbacks
import purchasing_dashboard.callbacks.all_callbacks  # pyright: ignore[reportUnusedImport]

server = app.server  # Expose the underlying Flask server for discovery by gunicorn/waitress

if __name__ == "__main__":
    if DEBUG_ENABLED:
        logger.info("Starting dashboard in debug mode...")
        app.run(
            debug=True,
            # avoid VSCode's periodic git fetch triggering a hot reload
            dev_tools_hot_reload=False,
            # dev_tools_hot_reload_interval=10,
            # dev_tools_hot_reload_watch_interval=5,
            # dev_tools_silence_routes_logging=False,
            **{
                "use_reloader": True,
                "exclude_patterns": ["*.git*", "*.venv*"],
                "reloader_type": "auto",
                "reloader_interval": 10.0,
            }
        )
    else:
        logger.info("Starting dashboard in production mode...")
        app.run(
            debug=False,
            dev_tools_hot_reload=False,
        )
