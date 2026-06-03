# Methods for calling the API
import requests
from datetime import datetime, timedelta
from typing import Any, ClassVar

from purchasing_dashboard.utils.environment_variables import API_URL
from dashboard_common.model.time_bucket import TimeBucket
import time
import random

from purchasing_dashboard.utils.logging import logger

# Define API endpoints


class Api:
    MULTIPLE_ORDER_FORECAST_ENDPOINT: ClassVar[str] = f"{API_URL}/items/orders/forecast"
    MULTIPLE_ORDER_HISTORY_ENDPOINT: ClassVar[str] = f"{API_URL}/items/orders/history"
    CUSTOMER_BREAKDOWN_ENDPOINT: ClassVar[str] = f"{API_URL}/items/customer-distribution"
    AVAILABLE_FORECAST_TYPES_ENDPOINT: ClassVar[str] = f"{API_URL}/items/orders/forecast-types"
    ITEM_IDS_ENDPOINT: ClassVar[str] = f"{API_URL}/items/ids"
    PRODUCT_IDS_ENDPOINT: ClassVar[str] = f"{API_URL}/products/ids"
    BUILT_OUT_ITEMS_ENDPOINT: ClassVar[str] = f"{API_URL}/products/{{}}/built-out-items"
    VENDOR_ITEMS_PURCHASED_ENDPOINT: ClassVar[str] = f"{API_URL}/vendor-items"
    OPEN_ORDERS_ENDPOINT: ClassVar[str] = f"{API_URL}/recent-orders"

    session = requests.Session()
    MAX_RETRIES: ClassVar[int] = 5
    BACKOFF_EXPONENT: ClassVar[float] = 2.0
    """
    The factor by which the wait time increases after each retry.
    """
    BACKOFF_FACTOR: ClassVar[float] = 0.6
    """
    Base wait time in seconds.
    """

    def request_with_retry(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Makes an HTTP request with retries and exponential backoff.

        Exponential backoff increases the wait time between retries exponentially,
        helping to reduce the load on the server and improve the chances of a successful request.
        For example, with a BACKOFF_FACTOR of 0.6, a BACKOFF_EXPONENT of 2, and MAX_RETRIES of 4,
        the wait times will be:

        - 1st retry: 0.6 * (2^0) = 0.6 seconds
        - 2nd retry: 0.6 * (2^1) = 1.2 seconds
        - 3rd retry: 0.6 * (2^2) = 2.4 seconds
        - 4th retry: 0.6 * (2^3) = 4.8 seconds
        """

        for attempt in range(self.MAX_RETRIES - 1):
            try:
                if method == "get":
                    res = self.session.get(endpoint, **kwargs)
                elif method == "post":
                    res = self.session.post(endpoint, **kwargs)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                res.raise_for_status()
                return res
            except requests.HTTPError as e:
                if e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    # Client error, do not retry
                    logger.error(
                        f"Client error {e.response.status_code} for {endpoint}: {e}. Not retrying.")
                    raise e
                wait = self.BACKOFF_FACTOR * \
                    (self.BACKOFF_EXPONENT ** attempt) + \
                    random.uniform(0, self.BACKOFF_FACTOR)
                logger.warning(
                    f"Attempt {attempt+1} failed for {endpoint}: {e}. Retrying in {wait:.2f}s...")
                time.sleep(wait)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise e
        raise AllRetriesFailedError(
            f"All {self.MAX_RETRIES} attempts failed for {endpoint}.")

    def make_get_request(self, endpoint: str, optional_params: dict = dict(), *required_params: Any) -> requests.Response:
        try:
            request_start_time = datetime.now()
            if (required_params):
                logger.info(
                    f"Making API GET request to {endpoint} with params {required_params}")
                endpoint = endpoint.format(*required_params)
            else:
                logger.info(f"Making API GET request to {endpoint}")
            res = self.request_with_retry(
                "get", endpoint, params=optional_params)
            res.raise_for_status()
            logger.debug(
                f"API GET request to {endpoint} took {datetime.now()-request_start_time}")
            return res.json()
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"API endpoint {endpoint} returned 404.")
                return None
            elif e.response is not None and 400 <= e.response.status_code < 500:
                logger.error(
                    f"When connecting to endpoint {endpoint} received Client Error {e.response.status_code}: {e} ")
                raise e
            logger.error(f"When connecting to endpoint {endpoint} received API Error: {e} ")
            raise e
        except Exception as e:
            logger.error(
                f"Upon attempting to connect to endpoint {endpoint}, received an error: {e} ")
            raise e

    def make_post_request(self, endpoint: str, data: dict) -> requests.Response:
        try:
            request_start_time = datetime.now()
            logger.info(
                f"Making API POST request to {endpoint} with data {data}")
            res = self.request_with_retry("post", endpoint, json=data)
            res.raise_for_status()
            logger.debug(
                f"API POST request to {endpoint} took {datetime.now()-request_start_time}")
            return res.json()
        except Exception as e:
            logger.error(
                f"When connecting to endpoint {endpoint} received API Error: {e} ")
            raise Exception(f"Failed to connect to API endpoint {endpoint}")

    def fetch_inventory_data(self) -> requests.Response:
        return self.make_get_request(Api.VENDOR_ITEMS_PURCHASED_ENDPOINT)

    def fetch_open_orders_data(self, open_only: bool = True) -> requests.Response:
        return self.make_get_request(
            Api.OPEN_ORDERS_ENDPOINT, 
            optional_params={"open_only": open_only}
            )

    def fetch_order_history(self, item_ids: str | list[str]) -> requests.Response:
        if isinstance(item_ids, str):
            item_ids = [item_ids]
        return self.make_post_request(Api.MULTIPLE_ORDER_HISTORY_ENDPOINT,
                                      {"item_ids": item_ids}
                                      )

    def fetch_order_forecast(self, item_ids: str | list[str], time_bucket: str, n_forecasts: int = 10, forecast_type: str = "auto") -> requests.Response:
        return self.make_post_request(
            Api.MULTIPLE_ORDER_FORECAST_ENDPOINT,
            {
                "item_ids": item_ids,
                "time_bucket": time_bucket,
                "n_forecasts": n_forecasts,
                "forecast_type": forecast_type
            }
        )

    def fetch_customer_breakdown(self, item_ids: list[str]) -> requests.Response:
        six_months_ago = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0) - timedelta(days=180)
        return self.make_post_request(
            Api.CUSTOMER_BREAKDOWN_ENDPOINT,
            {
                "item_ids": item_ids,
                "until": six_months_ago.strftime("%Y-%m-%d"),
                "average_by": TimeBucket.month.name
            }
        )

    def fetch_available_forecast_types(self, item_ids: list[str]) -> requests.Response:
        return self.make_post_request(
            Api.AVAILABLE_FORECAST_TYPES_ENDPOINT,
            {"item_ids": item_ids}
        )

    def fetch_item_ids(self) -> requests.Response:
        return self.make_get_request(Api.ITEM_IDS_ENDPOINT)

    def fetch_product_ids(self) -> requests.Response:
        return self.make_get_request(
            Api.PRODUCT_IDS_ENDPOINT
        )
    
    def fetch_built_out_items(self, product_id: str) -> requests.Response:
        return self.make_get_request(
            Api.BUILT_OUT_ITEMS_ENDPOINT,
            {},
            product_id
        )

class AllRetriesFailedError(Exception):
    pass


api = Api()
