import pytest
import pandas as pd
from datetime import datetime
from dashboard_common.model.forecast import Forecast, ForecastType
from dashboard_common.model.time_bucket import TimeBucket

def make_valid_df():
    return pd.DataFrame({
        "units": [10, 20, 30],
        "time": [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
    })

def test_WHEN_received_type_is_auto_THEN_raise_value_error():
    df = make_valid_df()
    with pytest.raises(ValueError, match="Received forecast type cannot be 'auto'"):
        Forecast(
            item_codes=frozenset(["A"]),
            initiated_type=ForecastType.auto,
            received_type=ForecastType.auto,
            num_forecasted_points=3,
            time_bucket=TimeBucket("day"),
            time_initiated=datetime.now(),
            time_computed=datetime.now(),
            goodness_of_fit={"rmse": 1.0},
            forecast_data=df
        )

def test_WHEN_forecast_data_missing_units_column_THEN_raise_value_error():
    df = pd.DataFrame({
        "time": [datetime(2024, 1, 1), datetime(2024, 1, 2)]
    })
    with pytest.raises(ValueError, match="Missing required column for 'Units'"):
        Forecast(
            item_codes=frozenset(["A"]),
            initiated_type=ForecastType.basic,
            received_type=ForecastType.linear,
            num_forecasted_points=2,
            time_bucket=TimeBucket("day"),
            time_initiated=datetime.now(),
            time_computed=datetime.now(),
            goodness_of_fit={"rmse": 1.0},
            forecast_data=df
        )

def test_WHEN_units_column_is_not_numeric_THEN_raise_value_error():
    df = pd.DataFrame({
        "units": ["a", "b", "c"],
        "time": [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
    })
    with pytest.raises(ValueError, match="The 'Units' column must be numeric."):
        Forecast(
            item_codes=frozenset(["A"]),
            initiated_type=ForecastType.basic,
            received_type=ForecastType.linear,
            num_forecasted_points=3,
            time_bucket=TimeBucket("day"),
            time_initiated=datetime.now(),
            time_computed=datetime.now(),
            goodness_of_fit={"rmse": 1.0},
            forecast_data=df
        )

def test_WHEN_time_column_is_not_datetime_THEN_raise_value_error():
    df = pd.DataFrame({
        "units": [1, 2, 3],
        "time": ["not_a_date", "still_not_a_date", "nope"]
    })
    with pytest.raises(ValueError, match="The 'Time' column must be datetime or timestamp"):
        Forecast(
            item_codes=frozenset(["A"]),
            initiated_type=ForecastType.basic,
            received_type=ForecastType.linear,
            num_forecasted_points=3,
            time_bucket=TimeBucket("day"),
            time_initiated=datetime.now(),
            time_computed=datetime.now(),
            goodness_of_fit={"rmse": 1.0},
            forecast_data=df
        )

def test_WHEN_aliases_are_used_for_columns_THEN_columns_are_renamed(caplog):
    df = pd.DataFrame({
        "forecast": [1, 2, 3],
        "orderdate": [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]
    })
    f = Forecast(
        item_codes=frozenset(["A"]),
        initiated_type=ForecastType.basic,
        received_type=ForecastType.linear,
        num_forecasted_points=3,
        time_bucket=TimeBucket("day"),
        time_initiated=datetime.now(),
        time_computed=datetime.now(),
        goodness_of_fit={"rmse": 1.0},
        forecast_data=df
    )
    assert "Units" in f.forecast_data.columns
    assert "Time" in f.forecast_data.columns

@pytest.mark.skip(reason="This test is designed to always fail.")
def test_alwaysfails():
    raise ValueError("This test is designed to always fail.")