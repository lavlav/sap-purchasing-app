from data_api.forecast.generate_predictions import generate_forecast_predictions, generate_goodness_of_fit_metrics
from sklearn.linear_model import LinearRegression
from data_api.utils.data_manipulation import prepare_data_points
from data_api.utils.data_manipulation import prepare_training_test_split
from data_api.utils.logging import logger



def get_linear_model_prediction(item_id: str, period: str, n_forecasts: int, augment: bool = True):
    X, y = prepare_data_points(
        item_id, period, resample=True, augment_time_series=augment)
    # If it was augmented, drop all non-numeric columns
    if augment:
        X = X.select_dtypes(include=['number'])
    
    X_train, X_test, y_train, y_test = prepare_training_test_split(item_id, period, X, y)
    logger.debug(f"Training linear model for item {item_id}.")
    model = LinearRegression()
    model.fit(X_train, y_train)
    logger.debug(f"Linear model coefficients: {model.coef_}")
    goodness_of_fit = generate_goodness_of_fit_metrics(model, X_test, y_test)
    predictions = generate_forecast_predictions(period, n_forecasts, X, model, augment=augment, include_non_numeric=False)
    r_2 = model.score(X_test, y_test)
    if r_2 and -1 <= r_2 <= 1:
        goodness_of_fit["R^2"] = r_2
    else:
        logger.warning(f"Computed R^2 value is invalid: {r_2}. Omitting from results.")
    return predictions, goodness_of_fit

