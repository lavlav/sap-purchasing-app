from datetime import datetime
import json
import traceback
from dash import callback_context, set_props
from purchasing_dashboard.layout.common.error_modal import ErrorModal
from purchasing_dashboard.utils.logging import logger

def handle_callback_error(err: Exception) -> None:
    """
    Handle errors that occur in Dash callbacks by displaying an error modal.
    """
    set_props(ErrorModal.ids.container("error-modal"), {"className": "error-modal"})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exception_info = f"Exception info: {err.__class__.__name__}: {err}"
    traceback_info = f"Traceback info: {traceback.format_exc()}"
    input_info = f"Input info: {json.dumps(callback_context.triggered)}"
    debugging_info = "\n".join([now, exception_info, traceback_info, input_info])
    logger.error(f"An error occurred in a callback: {err}")
    logger.error(f"The user was shown the following:\n{debugging_info}")
    set_props(ErrorModal.ids.exception_text("error-modal"), {"children": debugging_info})
    # don't raise or return anything, just show the modal
