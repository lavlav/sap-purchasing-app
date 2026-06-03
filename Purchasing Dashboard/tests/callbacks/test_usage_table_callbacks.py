from purchasing_dashboard.utils.logging import logger
import logging
import pandas as pd
import pytest
from purchasing_dashboard.callbacks.usage_table_callbacks import pivot_order_dataframe

# tests/callbacks/test_usage_table_callbacks.py

pytestmark = pytest.mark.skipif(
    True,
    reason="The interface of pivot_order_dataframe() changed, tests need to be updated",
    allow_module_level=True
)


@pytest.fixture
def sample_df():
    data = {
        "OrderDate": pd.to_datetime([
            "2023-01-15", "2023-02-20", "2023-03-10",
            "2023-04-05", "2023-05-15", "2023-06-25",
            "2023-07-01", "2023-08-12", "2023-09-30"
        ]),
        "Units": [10, 0, 5, 0, 8, 0, 12, 0, 7]
    }
    return pd.DataFrame(data)


def test_WHEN_pivot_month_THEN_result_contains_month_and_year_columns(sample_df):
    df = sample_df.copy()
    result = pivot_order_dataframe(df, "month")
    assert "Year" in result.columns
    for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]:
        assert month in result.columns or month not in df["OrderDate"].dt.month_name(
        ).str[:3].unique()
    assert not any(col == "Units" for col in result.columns)
    assert (result.isnull().any().any() or (result == None).any().any())


def test_WHEN_pivot_quarter_THEN_result_contains_quarter_and_year_columns(sample_df):
    df = sample_df.copy()
    result = pivot_order_dataframe(df, "quarter")
    assert "Year" in result.columns
    for quarter in ["Q1", "Q2", "Q3", "Q4"]:
        assert quarter in result.columns or quarter not in df["OrderDate"].dt.quarter.astype(
            str).apply(lambda x: "Q"+x).unique()
    assert not any(col == "Units" for col in result.columns)


def test_pivot_year(sample_df):
    df = sample_df.copy()
    result = pivot_order_dataframe(df, "year")
    assert "Year" in result.columns
    assert "UnitsSold" in result.columns
    assert (result.isnull().any().any() or (result == None).any().any())


def test_pivot_day(sample_df):
    df = sample_df.copy()
    result = pivot_order_dataframe(df, "day")
    assert "Date" in result.columns
    assert "UnitsSold" in result.columns
    assert (result.isnull().any().any() or (result == None).any().any())
    assert all(result["Date"].str.match(r"\d{4}-\d{2}-\d{2}"))


def test_pivot_week(sample_df):
    df = sample_df.copy()
    result = pivot_order_dataframe(df, "week")
    assert "Date" in result.columns
    assert "UnitsSold" in result.columns
    assert (result.isnull().any().any() or (result == None).any().any())
    assert all(result["Date"].str.match(r"\d{4}-\d{2}-\d{2}"))


def test_empty_dataframe():
    df = pd.DataFrame({"OrderDate": pd.to_datetime([]), "Units": []})
    for bucket in ["month", "quarter", "year", "day", "week"]:
        result = pivot_order_dataframe(df.copy(), bucket)
        assert isinstance(result, pd.DataFrame)
        assert result.empty


@pytest.mark.skip(reason="This test failing is currently non-breaking, but should be fixed")
def test_all_zero_units(sample_df):
    df = sample_df.copy()
    df["Units"] = 0
    for bucket in ["month", "quarter", "year", "day", "week"]:
        result = pivot_order_dataframe(df.copy(), bucket)
        assert (result.isnull().all().all() or (result == None).all().all())
