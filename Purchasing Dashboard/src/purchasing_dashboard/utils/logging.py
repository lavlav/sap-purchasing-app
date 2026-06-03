from datetime import datetime
import logging


logger = logging.getLogger()
if (logger.hasHandlers()):
    logger.handlers.clear()
output = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d [%(levelname)s] %(message)s")
output.setFormatter(formatter)
logger.addHandler(output)


def log_last_loaded(data_name: str, last_updated_ms: int):
    since_last_modified_str = str(int((datetime.now() - datetime.fromtimestamp(last_updated_ms/1000)).total_seconds()))
    logger.info(f"{data_name} already fetched into session memory. Last: {since_last_modified_str}s ago")


def log_stale(data_name: str, last_updated_ms: int):
    seconds_since_last_modified = int((datetime.now() - datetime.fromtimestamp(last_updated_ms/1000)).total_seconds())
    logger.info(f"{data_name} is stale and needs to be re-fetched. Last: {seconds_since_last_modified}s")