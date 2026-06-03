# class TFCRequest(TypedDict):
import pandas
from theforecastingcompany import TFCClient
from theforecastingcompany.utils import TFCModels

from data_api.forecast.generate_predictions import _generate_goodness_of_fit_metrics
from data_api.utils.data_manipulation import prepare_data_points
from dashboard_common.model.time_bucket import TimeBucket

from data_api.utils.logging import logger


client = TFCClient()

def get_tfc_api_prediction(item_ids: tuple[str], period: str, n_forecasts: int):
    train_df = prepare_data_points(
        item_ids, 
        period, 
        resample=True, 
        augment_time_series=False,
        as_dataframe=True
        )
    # TODO #74: handle multiple item_ids
    train_df["ItemCode"] = item_ids[0]
    train_df["OrderDate"] = pandas.to_datetime(train_df["OrderDate"], unit='s')
    logger.debug(f"Training data: {train_df.head(5)}")
    logger.debug(f"Data prepared for TFC API for item {item_ids}: {train_df.shape}\nCols: {train_df.columns}.")
    # train_df.set_index("OrderDate", inplace=True)
    model = TFCModels.TabPFN_TS
    logger.debug(f"Available TFC model: {model}")
    dates = train_df["OrderDate"].sort_values().unique()
    split_time = dates[int(len(dates) * 0.8)]
    pd_freq = TimeBucket(period).get_resample_rule()[0]
    logger.debug(f"Split time for cross-validation: {split_time}; freq: {pd_freq}")
    logger.debug(f"Querying TFC API for item {item_ids} with model {model}, period {period}, n_forecasts {n_forecasts}.")
    prediction_data = client.forecast(
        train_df=train_df,
        model=model,
        horizon=n_forecasts,
        freq=pd_freq,
        id_col="ItemCode",
        date_col="OrderDate",
        target_col=f"Units"
    )
    num_forecasts_required_to_cross_validate = len(dates) - list(dates).index(split_time) - 1
    logger.debug(f"Cross-validating for item {item_ids} with model {model}, period {period}, n_forecasts {n_forecasts}.")
    cross_validation_data = client.cross_validate(
        train_df=train_df,
        model=model,
        horizon=num_forecasts_required_to_cross_validate,
        freq=pd_freq,
        id_col="ItemCode",
        date_col="OrderDate",
        target_col=f"Units",
        fcds=[split_time],
    )
    logger.debug(f"TFC-provided cross-validation data: {cross_validation_data.head(5)}")
    goodness_of_fit = _generate_goodness_of_fit_metrics(
        cross_validation_data[str(model)], 
        cross_validation_data["Units"]
    )
    predictions = prediction_data[["OrderDate", str(model)]] \
        .rename(columns={str(model): "Units"})
    predictions["Prediction"] = pandas.Series([True] * len(predictions))
    predictions["OrderDate"] = predictions["OrderDate"].astype("int64") // 10**9
    return predictions.to_dict(orient="records"), goodness_of_fit