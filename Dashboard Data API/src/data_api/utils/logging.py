import logging
from data_api.utils.environment_variables import LOG_LEVEL
def _init_logger():
    logger = logging.getLogger("uvicorn")
    logger.setLevel(LOG_LEVEL)

    return logger

logger = _init_logger()