import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_database_engines():
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        mock_engine = MagicMock(name="MockEngine")
        mock_create_engine.return_value = mock_engine
        yield mock_engine

@pytest.fixture(autouse=True)
def mock_tfc_client():
    with patch("theforecastingcompany.TFCClient") as mock_constructor:
        mock_client = MagicMock(name="MockTFCClient")
        mock_constructor.return_value = mock_client
        yield mock_client