import pytest
from sqlalchemy import text

@pytest.fixture(scope="session", autouse=True)
def clear_all_tables_after_session(engine):
    yield  # Run all tests first
    tables = [
        "POR1", "PDN1", "INV1", "OINV", "OPOR", "OITW", "OITM", "OCRD", "OSPP"
    ]
    with engine.begin() as conn:
        for table in tables:
            conn.execute(text(f"DELETE FROM {table}"))