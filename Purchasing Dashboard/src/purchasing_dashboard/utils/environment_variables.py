import os
import json
from dotenv import load_dotenv
from dashboard_common.exceptions import MissingEnvironmentVariableError
import logging

from purchasing_dashboard.utils.logging import logger

def load_secrets(secrets_file):
    """Load secrets from a JSON file."""
    if os.path.exists(secrets_file):
        with open(secrets_file, "r") as file:
            return json.load(file)
    raise FileNotFoundError(f"Secrets file not found: {secrets_file}")

load_dotenv()

# Environment variables for the purchasing dashboard application
try:
    DEBUG_ENABLED = os.environ["DEBUG_ENABLED"].lower() in ("true", "1", "yes")
    """REQUIRED: Whether or not debug mode is enabled."""

    SECRETS_FILE = os.environ["SECRETS_FILE"]
    """REQUIRED: Path to the Docker secrets json file."""

    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
    """Logging level for the application."""

    # Set the logger level immediately
    logger.setLevel(LOG_LEVEL)

    MAINTAINER_CONTACT = os.getenv("MAINTAINER_CONTACT", "the maintainer")
    """Email address of the application maintainer. Used in error messages. Defaults to "the maintainer"."""

    MAINTAINER_CONTACT_LINK: str = os.getenv("MAINTAINER_CONTACT_LINK", "")
    """HTML mailto link for the application maintainer. Used in error messages. If unspecified, no link will be provided.

    Example: mailto:lchellaram@ocusoft.com"""

    TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
    """IANA time zone for the application. Defaults to America/Chicago, since that's the timezone OCuSOFT is in."""

    GET_SECRETS_FROM_ENVIRONMENT_VARIABLES = os.getenv("GET_SECRETS_FROM_ENVIRONMENT_VARIABLES", "False").lower() in ("true", "1", "yes")
    """Whether to use secrets for sensitive information. Defaults to False. Read the README for more information."""
except KeyError as e:
    raise MissingEnvironmentVariableError(f"Missing required environment variable: {e}")

# Load secrets
try:
    if not GET_SECRETS_FROM_ENVIRONMENT_VARIABLES:
        secrets = load_secrets(SECRETS_FILE)
    else:
        logger.warning("Getting secrets from environment variables instead of file.")
        secrets = os.environ

    BASIC_AUTH_USERNAME = secrets["BASIC_AUTH_USERNAME"]
    """REQUIRED: Username for HTTP basic authentication."""

    BASIC_AUTH_PASSWORD = secrets["BASIC_AUTH_PASSWORD"]
    """REQUIRED: Password for HTTP basic authentication."""

    API_URL = secrets["API_URL"]
    """REQUIRED: Base URL for the Data API."""
except KeyError as e:
    raise MissingEnvironmentVariableError(f"Missing required secret: {e}")