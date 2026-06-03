"""
Fixtures for integration tests.

Setup and teardown assumes that the mock-data database is running and accessible.
"""
import pytest
import requests

API_URL = "http://localhost:8000"

@pytest.fixture(scope="session")
def api_base_url():
    # Optionally, wait for the API to be up
    import time
    for _ in range(30):
        try:
            r = requests.get(f"{API_URL}/docs")
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(1)
    return API_URL

@pytest.fixture
def mock_card_code():
    return "V-01"

@pytest.fixture
def mock_item_code():
    return "000-00-001"