from math import isfinite
from data_api.utils.logging import logger
from data_api.utils.data_manipulation import generate_forecast_input

import numpy as np
from sklearn.metrics import root_mean_squared_error

def generate_goodness_of_fit_metrics(model, X_test, y_test):
    logger.debug(f"Model score: {model.score(X_test, y_test)}")
    return _generate_goodness_of_fit_metrics(model.predict(X_test), y_test)

def _generate_goodness_of_fit_metrics(predictions: list, actual: list):
    goodness_of_fit = {}
    # Calculate RMSE and MAPE
    rmse = root_mean_squared_error(actual, predictions)
    goodness_of_fit["RMSE"] = float(rmse)
    mape = np.mean(np.abs((actual - predictions) / actual)) * 100
    if np.isfinite(mape) and not np.isnan(mape):
        goodness_of_fit["MAPE"] = float(mape)
    logger.debug(f"RMSE: {rmse}, MAPE: {mape}")
    return goodness_of_fit

def generate_forecast_predictions(period, n_forecasts, X, model, augment=True, include_non_numeric=True):
    """
    Generates predictions and evaluates goodness of fit metrics using the trained model.
    """
    # Evaluate the model's performance on the test set
    logger.debug(f"Columns used for prediction: {X.columns.tolist()}")

    # Predictions for the next n_forecasts periods
    X_future = generate_forecast_input(
        X.loc[X["OrderDate"].idxmax()], 
        n_forecasts, 
        period, 
        augment=augment, 
        include_non_numeric=include_non_numeric
    )
    y_pred = model.predict(X_future)
    predictions = [
            {"OrderDate": int(X_future.iloc[i]["OrderDate"]), "Units": float(y_pred[i]), "Prediction": True}
            for i in range(n_forecasts)
        ]

    return predictions