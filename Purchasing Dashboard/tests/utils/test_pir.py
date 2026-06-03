

from datetime import datetime
from unittest.mock import patch
from purchasing_dashboard.utils.pir import append_date_columns, generate_pir_dataframe, pivot_forecast_dataframe
from dashboard_common.model.forecast import Forecast, ForecastSet
import pandas as pd
import pytest

@pytest.fixture
def mock_forecast_set():
    with patch("dashboard_common.model.forecast.Forecast") as MockForecast:
        mock_forecast1 = MockForecast()
        mock_forecast1.forecast_data = pd.DataFrame({
            "Time": pd.date_range(start="2023-05-01", periods=12, freq="M"),
            "Units": [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650]
        })
        mock_forecast1.num_forecasted_points = 12

        mock_forecast2 = MockForecast()
    mock_forecast2.forecast_data = pd.DataFrame({
        "Time": pd.date_range(start="2023-05-01", periods=12, freq="M"),
        "Units": [110, 160, 210, 260, 310, 360, 410, 460, 510, 560, 610, 660]
    })
    mock_forecast2.num_forecasted_points = 12

    forecasts = {"ITEM123": mock_forecast1, "ITEM456": mock_forecast2}
    return ForecastSet.from_dict(forecasts)

def test_append_date_columns():
    result = append_date_columns(
        start_date=datetime(2023, 5, 3),
        num_months=10
    )
    assert result == [
        "MaterialID", "Plant", "MRPArea", "Version", "ReqType", "VersionActive", "ReqPlan", "ReqSeg", "UoM",
        "M05.2023", "M06.2023", "M07.2023", "M08.2023", "M09.2023", "M10.2023", "M11.2023", "M12.2023",
        "M01.2024", "M02.2024"
    ]

def test_pivot_forecast_dataframe():
    df = pd.DataFrame({
        "Time": pd.date_range(start="2023-05-01", periods=10, freq="MS"),
        "Units": [100, 150, 200, 250, 300, 350, 400, 450, 500, 550]
    })
    item_code = "ITEM123"
    result = pivot_forecast_dataframe(df, item_code)
    assert result["MaterialID"].iloc[0] == item_code
    assert "M05.2023" in result.columns
    assert result["M05.2023"].iloc[0] == 100

def test_generate_pir_dataframe():
    def test_generate_pir_dataframe_basic(mock_forecast_set):
        item_codes = ["ITEM123", "ITEM456"]
        start_date = datetime(2023, 5, 1)
        num_months = 12
        df = generate_pir_dataframe(item_codes, mock_forecast_set, start_date, num_months)
        # Check columns
        expected_columns = [
            "MaterialID", "Plant", "MRPArea", "Version", "ReqType", "VersionActive", "ReqPlan", "ReqSeg", "UoM",
            "M05.2023", "M06.2023", "M07.2023", "M08.2023", "M09.2023", "M10.2023", "M11.2023", "M12.2023",
            "M01.2024", "M02.2024", "M03.2024", "M04.2024"
        ]
        assert list(df.columns) == expected_columns
        # Check that both items are present
        assert set(df["MaterialID"]) == {"ITEM123", "ITEM456"}
        # Check values for a known month
        assert df.loc[df["MaterialID"] == "ITEM123", "M05.2023"].iloc[0] == 100
        assert df.loc[df["MaterialID"] == "ITEM456", "M05.2023"].iloc[0] == 110

    def test_generate_pir_dataframe_missing_forecast(mock_forecast_set):
        item_codes = ["ITEM123", "ITEM789"]  # ITEM789 does not exist
        with pytest.raises(ValueError, match="No forecast data available for item code: ITEM789"):
            generate_pir_dataframe(item_codes, mock_forecast_set, datetime(2023, 5, 1), 12)

    def test_generate_pir_dataframe_insufficient_months(mock_forecast_set):
        # Patch one forecast to have fewer points
        mock_forecast = mock_forecast_set.get("ITEM123", None)
        mock_forecast.num_forecasted_points = 5
        item_codes = ["ITEM123"]
        with pytest.raises(ValueError, match="Forecast data for item code ITEM123 does not cover the required number of months: 12"):
            generate_pir_dataframe(item_codes, mock_forecast_set, datetime(2023, 5, 1), 12)