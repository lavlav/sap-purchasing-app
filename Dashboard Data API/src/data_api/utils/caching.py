import asyncio
from cachetools import TTLCache
import datetime
import sys
from data_api.utils.logging import logger

# TODO #74: determine this empirically/dynamically
MAX_CACHE_ENTRIES=400

class LoggingTTLCache(TTLCache):
    """
    A TTLCache that logs cache operations for debugging purposes.
    """
    def __init__(self, name, *args, **kwargs):
        kwargs["maxsize"] = kwargs.get("maxsize", MAX_CACHE_ENTRIES)
        self.name = name
        super().__init__(*args, **kwargs)
        logger.debug(f"Initialized LoggingTTLCache with name={name}, maxsize={self.maxsize} and ttl={self.ttl}")

    def __setitem__(self, key, value, cache_setitem=TTLCache.__setitem__):
        logger.debug(f"{self.name} - Setting cache key: {key} at time {datetime.datetime.now()}")
        super().__setitem__(key, value, cache_setitem=cache_setitem)

    def __getitem__(self, key, cache_getitem=TTLCache.__getitem__):
        logger.debug(f"{self.name} - Getting cache key: {key} at time {datetime.datetime.now()}")
        return super().__getitem__(key, cache_getitem=cache_getitem)

    def __delitem__(self, key, cache_delitem=TTLCache.__delitem__):
        logger.debug(f"{self.name} - Deleting cache key: {key} at time {datetime.datetime.now()}")
        super().__delitem__(key, cache_delitem=cache_delitem)

def _big_sql_cache(name="unnamed cache (big)"):
    return LoggingTTLCache(name=name, ttl=datetime.timedelta(hours=24), timer=datetime.datetime.now)

def _small_sql_cache(name="unnamed cache (small)"):
    return LoggingTTLCache(name=name, ttl=datetime.timedelta(hours=1), timer=datetime.datetime.now)

def _forecast_cache(name="unnamed cache (forecast)"):
    return LoggingTTLCache(name=name, ttl=datetime.timedelta(minutes=30), timer=datetime.datetime.now)

ITEM_CODES_AND_NAMES_CACHE=_small_sql_cache("item codes and names cache")
ORDER_HISTORY_CACHE=_big_sql_cache("order history cache")
RECENT_ORDERS_CACHE=_small_sql_cache("recent orders cache")
FORECAST_CACHE=_forecast_cache("forecast cache")
PURCHASING_TABLE_CACHE=_big_sql_cache("purchasing table cache")
PRODUCTS_CACHE=_small_sql_cache("products cache")
PRODUCT_IDS_CACHE=_small_sql_cache("product ids cache")

async def background_log_cache_status():
    while True:
        log_cache_status()
        await asyncio.sleep(1800)  # Log every 30 minutes

def log_cache_status():
    logger.info("Cache Status:")
    for cache in [
        ITEM_CODES_AND_NAMES_CACHE,
        ORDER_HISTORY_CACHE,
        RECENT_ORDERS_CACHE,
        FORECAST_CACHE,
        PURCHASING_TABLE_CACHE,
    ]:
        total_size = sum(sys.getsizeof(v) for v in cache.values())
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.2f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"

        logger.info(f"{cache.name}: {len(cache)} entries, size={size_str}")