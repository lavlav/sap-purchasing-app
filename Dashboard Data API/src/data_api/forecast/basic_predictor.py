from data_api.forecast.linear_predictor import get_linear_model_prediction


def get_basic_prediction(item_id: str, period: str, n_forecasts: int):
    """
    Generates a basic prediction using random values.
    This is a placeholder for more complex models.
    """
    return get_linear_model_prediction(item_id, period, n_forecasts, augment=False)