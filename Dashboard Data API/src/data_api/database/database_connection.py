from sqlalchemy import create_engine

from data_api.utils.environment_variables import HISTORICAL_DATABASE_URL, SAP_DATABASE_URL

sap_database_engine = create_engine(SAP_DATABASE_URL, echo=False)
historical_database_engine = create_engine(HISTORICAL_DATABASE_URL, echo=False)
# TODO #74: use sessions and ORM instead of raw SQL queries
# SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=sap_database_engine)