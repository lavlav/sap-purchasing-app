import json
import os
from dotenv import load_dotenv
from dashboard_common.exceptions import MissingEnvironmentVariableError
# don't use data_api.utils.logging here since it depends on the LOG_LEVEL variable
import logging
logger = logging.getLogger("uvicorn")


def load_secrets(SECRETS_FILE_NAME):
    """ Load Docker secrets from the secrets file. """
    return json.load(open(SECRETS_FILE_NAME, "r")) if os.path.exists(SECRETS_FILE_NAME) else {}

load_dotenv()

try:
    # Load secrets from the Docker secret file
    SECRETS_FILE = os.environ["SECRETS_FILE"]
    """REQUIRED: Path to the JSON file containing secrets."""
    
    DEBUG_ENABLED=os.getenv("DEBUG_ENABLED", "False").lower() in ("true", "1", "t")
    """Enable debug mode for the application. Defaults to False."""

    LOG_LEVEL=os.getenv("LOG_LEVEL", "DEBUG").upper()
    """Logging level for the application. Defaults to DEBUG."""

    GET_SECRETS_FROM_ENVIRONMENT_VARIABLES = os.getenv("GET_SECRETS_FROM_ENVIRONMENT_VARIABLES", "False").lower() in ("true", "1", "yes")
    """Whether to use secrets for sensitive information. 
Read the README for more information on when to set this. 
Defaults to False."""

    VENDOR_DATA_CUSTOM_CONDITION = os.getenv("VENDOR_DATA_CUSTOM_CONDITION", "1=1")
    """(#74) SQL Condition to filter vendors for vendor data.
See UNIT_SALES_TABLE_QUERY for information on what tables are available.
Defaults to "1=1" (no filtering)."""

    PRODUCTS_CUSTOM_CONDITION = os.getenv("PRODUCTS_CUSTOM_CONDITION", "1=1")
    """(#74) SQL Condition to filter products for product list.
See PRODUCTS_QUERY for information on what tables are available.
Defaults to "1=1" (no filtering)."""

    TFC_ENABLED = os.getenv("TFC_API_KEY", "") != ""
    """Whether to enable TFC integration. Defaults to False."""
except KeyError as e:
    raise KeyError(f"Environment variable not set: {e}")

try:
    if not GET_SECRETS_FROM_ENVIRONMENT_VARIABLES:
        secrets = load_secrets(SECRETS_FILE)
    else:
        logger.warning("Getting secrets from environment variables instead of file.")
        secrets = os.environ

    HISTORICAL_DATABASE_URL=secrets["HISTORICAL_DATABASE_URL"]
    """REQUIRED. Database URL for the historical data."""

    SAP_DATABASE_URL=secrets["SAP_DATABASE_URL"]
    """REQUIRED. Database URL for the SAP data."""
except KeyError as e:
    suffix = "an environment variable" if GET_SECRETS_FROM_ENVIRONMENT_VARIABLES else f"{SECRETS_FILE}"
    raise MissingEnvironmentVariableError(f"Required secret not found in {suffix}: {e}")