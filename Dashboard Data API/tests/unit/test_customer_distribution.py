import numpy
import pytest
from unittest.mock import patch, MagicMock

with patch("sqlalchemy.create_engine") as mock_create_engine, \
    patch("theforecastingcompany.TFCClient") as mock_tfc_constructor:
    mock_create_engine.return_value = MagicMock(name="MockEngine")
    mock_tfc_client = MagicMock(name="MockTFCClient")
    mock_tfc_constructor.return_value = mock_tfc_client
    import pandas
    from data_api import get_historical_orders_for_item
    from fastapi.testclient import TestClient
    from data_api.api_main import app
    from dashboard_common.model.customer_distribution import CustomerDistribution

client = TestClient(app)

# Fixture for mock order data


@pytest.fixture
def mock_order_data():
    return pandas.DataFrame({
        "ItemCode": ["123", "123", "123", "456"],
        "AccountType": ["A", "A", "B", "B"],
        "OrderDate": [numpy.datetime64(date) for date in
                      ["2023-01-01", "2023-02-01", "2023-02-01", "2023-03-01"]
                      ],
        "Units": [5, 10, 18, 20],
        "Sales": [70.0, 30.0, 50.0, 40.0],
    })

# Fixture for a mock CustomerDistribution model


@pytest.fixture
def mock_customer_distribution(monkeypatch, mock_order_data):
    return CustomerDistribution(
        item_ids=["123", "456"],
        customer_data=mock_order_data,
        total_units=15,
        total_sales=100.0,
        calculated_at=1234567890.0
    )


def test_no_item_ids():
    response = client.post(
        "/api/items/customer-distribution", json={"item_ids": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "No item IDs provided."


def test_multiple_item_ids(monkeypatch, mock_customer_distribution):
    monkeypatch.setattr(
        "data_api.api_main.get_customer_distribution_for_items",
        lambda item_ids, until, average_by: mock_customer_distribution
    )
    response = client.post("/api/items/customer-distribution",
                           json={"item_ids": ["123", "456"]})
    assert response.status_code == 200
    assert response.json()["item_ids"] == ["123", "456"]

@pytest.mark.skip(reason="Needs fixing after API changes")
def test_item_id_not_found(monkeypatch, mock_order_data):
    from dashboard_common.model.customer_distribution import CustomerDistribution
    import pandas

    empty_cd = CustomerDistribution(
        item_ids=["notfound"],
        customer_data=pandas.DataFrame([]),
        total_units=0,
        total_sales=0.0,
        calculated_at=1234567890
    )
    # Patch the function in the api_main module, not just the source module
    monkeypatch.setattr(
        "data_api.api_main.get_customer_distribution_for_items",
        lambda item_ids, until, average_by: empty_cd
    )
    response = client.post("/api/items/customer-distribution",
                           json={"item_ids": ["notfound"]})
    assert response.status_code == 404
    assert "No customer distribution" in response.json()["detail"]


def test_valid_item_id(monkeypatch, mock_customer_distribution):
    # Patch get_customer_distribution_for_items to return a non-empty DataFrame
    # Patch the function in the api_main module, not just the source module
    monkeypatch.setattr(
        "data_api.api_main.get_customer_distribution_for_items",
        lambda item_ids, until, average_by: mock_customer_distribution
    )
    response = client.post("/api/items/customer-distribution",
                           json={"item_ids": ["123", "456"]})
    assert response.status_code == 200
    assert response.json()["item_ids"] == ["123", "456"]
    assert response.json()["total_units"] == 15
    assert response.json()["total_sales"] == 100.0
