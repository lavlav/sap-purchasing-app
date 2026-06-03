import asyncio
from contextlib import asynccontextmanager
from multiprocessing import Value
from fastapi import FastAPI, Query, Request, Response, status

from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
import time

from data_api.database.item_names import read_item_codes_and_names
from data_api.database.order_history import read_order_history
from data_api.model.retrieve_customer_breakdown import RetrieveCustomerBreakdownRequest
from data_api.products import get_built_out_items, get_known_product_ids, read_products
from data_api.utils.caching import background_log_cache_status
from data_api.utils.environment_variables import DEBUG_ENABLED, LOG_LEVEL
from data_api.get_historical_orders_for_item import ItemMissingError, get_customer_distribution_for_items, get_recent_item_ids, post_recent_orders
from data_api.get_vendor_data import compute_vendor_data_table
from data_api.get_open_orders import get_recent_orders, read_recent_orders
from data_api.get_forecast_for_item import get_available_forecast_types, get_model_prediction

from data_api.model.retrieve_forecast_request import RetrieveForecastRequest
from data_api.model.retrieve_item_data import RetrieveItemDataRequest
from data_api.utils.logging import logger
from dashboard_common.model.forecast import ForecastType
from prometheus_fastapi_instrumentator import Instrumentator
from data_api.model.retrieve_product_ids import RetrieveProductIdsRequest

# Handle lifespan events
@asynccontextmanager
async def lifecycle(app: FastAPI):
    # Startup code
    logger.info("Starting Dashboard Data API.")
    # Don't preload caches in debug mode to avoid hitting the database unnecessarily
    # during hot reloads
    if not DEBUG_ENABLED:
        logger.info("Preloading caches...")
        read_item_codes_and_names()  # Preload item codes and names
        read_order_history()  # Preload order history
        read_recent_orders()  # Preload recent orders
        get_known_product_ids()  # Preload product ids
        compute_vendor_data_table()  # Preload vendor data
        logger.info("Caches preloaded.")
    else:
        logger.info("Skipping preload of caches in debug mode.")
    # Start background task to log cache status
    asyncio.create_task(background_log_cache_status())
    yield
    # Shutdown code
    logger.info("Shutting down Dashboard Data API.")


app = FastAPI(debug=DEBUG_ENABLED, lifespan=lifecycle)

class ResponseTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()  # Use perf_counter for more precise timing
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request to {request.url.path}: {e}")
            raise e
        process_time = time.perf_counter() - start_time
        logger.debug(
            f"Request to {request.url.path} took {process_time:.4f} seconds.")
        # Add the process time as a custom header
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(ResponseTimeMiddleware)

# Add Prometheus instrumentation

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
)
instrumentator.instrument(app).expose(app, include_in_schema=False)

# Add a simple exception handler for enum validation errors
# @app.exception_handler(ValueError)
async def validation_exception_handler(
    request: Request, exc: ValueError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": f"{exc}"})

# Define the various endpoints

@app.get("/api/vendor-items")
def get_inventory(
):
    return compute_vendor_data_table().to_json(orient="columns")


@app.get("/api/recent-orders")
def get_all_recent_orders(
    open_only: bool = Query(default=True, description="Filter by open only")
):
    # TODO #74: profile perfomance of orient="columns" vs orient="records"
    return get_recent_orders(open_only).to_json(orient="columns")

@app.post(
    "/api/items/orders/forecast-types"
)
def get_forecast_types(
    request: RetrieveItemDataRequest,
    response: Response
):
    """
    Get the available forecast types for forecasting orders for the given items.
    """
    try:
        item_ids = tuple(request.item_ids)
        if len(item_ids) == 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"detail": "No item IDs provided."}
        forecast_types = get_available_forecast_types(item_ids)
        return {"forecast_types": [ftype.value for ftype in forecast_types]}
    except ItemMissingError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": f"Items {e.missing_item_ids} not found."}


@app.get("/api/items/ids")
def get_item_ids():
    return get_recent_item_ids().to_dict(orient="records")


@app.post(
    path="/api/items/orders/history",
    description="Retrieve time-aggregated historical orders for a set of items.",
)
def post_items_order_history(
    request: RetrieveItemDataRequest,
    response: Response
):
    item_ids: tuple[str] = tuple(request.item_ids)
    if not item_ids:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": "No item IDs provided."}

    aggregated_order_history = post_recent_orders(item_ids)
    if (len(aggregated_order_history) == 0):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": "No orders found for the provided item IDs."}
    return aggregated_order_history


@app.post(
    path="/api/items/orders/forecast",
    description="Retrieve forecast data for a set of items.",
)
def post_items_forecast(
    request: RetrieveForecastRequest,
    response: Response
):
    item_ids: tuple[str] = tuple(request.item_ids)
    if not item_ids:
        logger.error("No item IDs provided for forecast request.")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": "No item IDs provided."}
    n_forecasts: int = request.n_forecasts
    time_bucket: str = request.time_bucket
    forecast_type: ForecastType = request.forecast_type
    prediction = get_model_prediction(
        item_ids, time_bucket, n_forecasts, forecast_type
    )
    if prediction is None or len(prediction) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": "No forecast data found for the provided item IDs."}
    logger.debug(f"Forecast prediction: {prediction}")
    return prediction


@app.post(
    path="/api/items/customer-distribution",
    description="Get the distribution of customer types who have ordered the given items in the last 5 years."
)
def post_customer_distribution(
    request: RetrieveCustomerBreakdownRequest,
    response: Response
):
    """
    Get the distribution of customer types who have ordered the given items up until the given date
    or the last 5 years, whichever is closer.
    """
    item_ids = tuple(request.item_ids)
    average_til = request.until
    average_by = request.average_by
    if not item_ids:
        response.status_code = status.HTTP_400_BAD_REQUEST 
        return {"detail": "No item IDs provided."}
    if average_til is None and average_by is not None:
        response.status_code = status.HTTP_400_BAD_REQUEST 
        return {"detail": "average_by provided without until."}
    try:
        customer_distribution = get_customer_distribution_for_items(item_ids, average_til, average_by)
    except ValidationError as e:
        logger.error(f"Validation error occurred: {e}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        for error in e.errors():
            if error['type'] == "too_long":
                return {
                    "detail": 
                    f"Item ID '{error['loc'][0]}' exceeds maximum length of {error['ctx']['max_length']}."
                    }
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"detail": f"Error getting customer distribution: {e}"}
    except ItemMissingError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"detail": f"Could not find any orders for items with codes: {', '.join(e.missing_item_ids)}."}
    if len(customer_distribution.customer_data) == 0:
        logger.warning(f"No customer distribution data found for items: {item_ids}")
    return customer_distribution

@app.get("/api/products/ids")
def get_product_ids():
    product_ids = get_known_product_ids()
    return product_ids.to_dict(orient="records")

@app.get("/api/products/{product_id}/built-out-items")
def get_built_items(product_id: str, years_back: int = 5):
    return get_built_out_items(product_id, years_back)