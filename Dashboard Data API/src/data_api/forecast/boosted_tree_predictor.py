from data_api.forecast.generate_predictions import generate_forecast_predictions, generate_goodness_of_fit_metrics
import xgboost as xgb
from sklearn.model_selection import train_test_split
from data_api.utils.data_manipulation import prepare_data_points, prepare_training_test_split
from data_api.utils.logging import logger


def get_boosted_tree_prediction(item_id: str, period: str, n_forecasts: int):
    """
    Trains a boosted tree (XGBoost) model and predicts future values.
    """
    X, y = prepare_data_points(item_id, period, resample=True)

    X_train, X_test, y_train, y_test = prepare_training_test_split(item_id, period, X, y)
    logger.debug(f"Training XGBoost model for item {item_id}.")

    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        max_depth=8,
        learning_rate=0.01,
        gamma=0.01,
        min_child_weight=3,
        colsample_bytree=20 / X_train.shape[1],
        # colsample_bytree=0.666,
        random_state=123,
        enable_categorical=True
        )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False) #
    logger.debug(f"XGBoost model feature importances:\n {model.feature_importances_}")
    goodness_of_fit = generate_goodness_of_fit_metrics(model, X_test, y_test)
    predictions = generate_forecast_predictions(period, n_forecasts, X, model)
    return predictions, goodness_of_fit