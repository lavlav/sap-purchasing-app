from threading import Condition, Lock
from cachetools import cached
import pandas as pd
from data_api.forecast.boosted_tree_predictor import get_boosted_tree_prediction
from data_api.forecast.linear_predictor import get_linear_model_prediction
from data_api.forecast.basic_predictor import get_basic_prediction
from data_api.forecast.tfc_predictor import get_tfc_api_prediction
from data_api.get_historical_orders_for_item import get_recent_orders
from data_api.utils.caching import FORECAST_CACHE
from data_api.utils.environment_variables import TFC_ENABLED
from data_api.utils.type_aliases import ItemId
from dashboard_common.model.forecast import ForecastType
from data_api.utils.logging import logger


# @cached(cache=FORECAST_CACHE,condition=Condition(Lock()))
def get_model_prediction(item_id: ItemId, period: int, n_forecasts: int, forecast_type: ForecastType | str = "linear"):
    if isinstance(forecast_type, str):
        forecast_type = ForecastType[forecast_type]
    match forecast_type:
        case ForecastType.linear:
            logger.info(
                f"Using linear model for item {item_id} with period {period} and {n_forecasts} forecasts.")
            predictions, goodness_of_fit = get_linear_model_prediction(
                item_id, period, n_forecasts)
        case ForecastType.boosted_tree:
            logger.info(
                f"Using boosted tree model for item {item_id} with period {period} and {n_forecasts} forecasts.")
            predictions, goodness_of_fit = get_boosted_tree_prediction(
                item_id, period, n_forecasts)
        case ForecastType.basic:
            logger.info(
                f"Using basic model for item {item_id} with period {period} and {n_forecasts} forecasts.")
            predictions, goodness_of_fit = get_basic_prediction(
                item_id, period, n_forecasts)
        case ForecastType.vendored:
            logger.info(
                f"Using TFC model for item {item_id} with period {period} and {n_forecasts} forecasts.")
            predictions, goodness_of_fit = get_tfc_api_prediction(
                item_id, period, n_forecasts)
        case _:
            # TODO #74: use some kind of selection process instead of defaulting to linear
            # Default to linear model if no valid type is provided
            logger.info(
                f"Using default linear model for item {item_id} with period {period} and {n_forecasts} forecasts.")
            predictions, goodness_of_fit = get_linear_model_prediction(
                item_id, period, n_forecasts)
            forecast_type = ForecastType.linear
    # Format the results for the API response
    results = format_result(
        predictions,
        goodness_of_fit,
        period,
        str(forecast_type)
    )
    return results

def format_result(predictions, goodness_of_fit, period, ftype):
    """ Formats the prediction results into a structured dictionary."""
    formatted = {
        "calculated_at": pd.Timestamp.now().as_unit("ms").timestamp(),
        "time_bucket": period,
        "goodness_of_fit": goodness_of_fit,
        "predictions": predictions,
        "forecast_type": ftype
    }
    return formatted


def get_available_forecast_types(item_ids: tuple[ItemId]) -> list[ForecastType]:
    """
    Returns the available forecast types for a list of item IDs.
    """
    if not item_ids:
        return []
    available_types = set(
        _get_available_forecast_types_individual(item_ids[0]))
    for item_id in item_ids[1:]:
        available_types.intersection_update(
            _get_available_forecast_types_individual(item_id))
    return sorted(list(available_types), key=lambda ft: ft.order)


def _get_available_forecast_types_individual(item_id: ItemId) -> list[str]:
    """
    Returns a list of available forecast types for a given item.
    """
    # Get the number of data points available for the item
    num_orders = get_recent_orders(
        item_id, ignore_missing_items=False).shape[0]
    if num_orders < 2:
        # Not enough data available for this item to reasonably forecast anything
        logger.warning(
            f"{num_orders} orders found for item {item_id}, not enough data to forecast.")
        types = []
    elif num_orders < 5:
        # Limited data, only basic is available
        types = [
            ForecastType.auto,
            ForecastType.basic
        ]
    else:
        # All forecast types are available
        types = [
            ForecastType.auto,
            ForecastType.basic,
            ForecastType.linear,
            ForecastType.boosted_tree,
        ]
        if TFC_ENABLED:
            types.append(ForecastType.vendored)
    return types
