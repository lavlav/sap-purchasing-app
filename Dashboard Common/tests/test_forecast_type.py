import pytest
from dashboard_common.model.forecast import ForecastType

def test_forecast_type_enum_values():
    assert ForecastType.auto.value == "auto"
    assert ForecastType.basic.value == "basic"
    assert ForecastType.linear.value == "linear"
    assert ForecastType.vendored.value == "vendored"
    assert ForecastType.boosted_tree.value == "boosted_tree"

def test_forecast_type_display_name():
    assert ForecastType.auto.get_display_name() == "Automatic"
    assert ForecastType.basic.get_display_name() == "Basic Regression"
    assert ForecastType.linear.get_display_name() == "Linear Regression"
    assert ForecastType.vendored.get_display_name() == "Advanced Regression"
    assert ForecastType.boosted_tree.get_display_name() == "Boosted Tree"

def test_forecast_type_order():
    assert ForecastType.auto.order == 1
    assert ForecastType.basic.order == 2
    assert ForecastType.linear.order == 3
    assert ForecastType.vendored.order == 4
    assert ForecastType.boosted_tree.order == 5

def test_forecast_type_str():
    assert str(ForecastType.auto) == "auto"
    assert str(ForecastType.basic) == "basic"
    assert str(ForecastType.linear) == "linear"
    assert str(ForecastType.vendored) == "vendored"
    assert str(ForecastType.boosted_tree) == "boosted_tree"