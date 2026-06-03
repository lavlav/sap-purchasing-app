import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from purchasing_dashboard.utils.environment_variables import TIMEZONE


def truncate_string(text: str, max_length: int, suffix: str = "...", space_lookback: int | None = None):
    """
    Truncates a string if its length exceeds max_length,
    optionally adding a suffix to indicate truncation.

    Args:
        text (str): The string to truncate.
        max_length (int): The maximum allowed length for the string.
        suffix (str, optional): The string to append if truncation occurs.
                                 Defaults to "...".
        space_lookback (int | None, optional): If provided, looks back for the last space
                                                after truncating to avoid cutting words.
                                                Defaults to None.
    Returns:
        str: The truncated string.
    """
    if len(text) > max_length:
        # Adjust max_length to account for the suffix length
        truncated_length = max_length - len(suffix)
        if space_lookback is not None:
            space_list = list(re.finditer(r'\s', text[:truncated_length]))
            last_space = space_list[-1].start() if space_list else -1
            truncated_length = last_space if truncated_length - last_space < space_lookback else truncated_length
        # Ensure truncated_length is not negative
        if truncated_length < 0:
            truncated_length = 0
        return text[:truncated_length] + suffix
    else:
        return text
    
def stringify_dash_id(id: dict | str) -> str:
    """
    Converts a Dash component ID to a string representation. Useful for HTML attributes
    that expect a string ID, but that you want to point to a Dash component.

    Args:
        id: A dictionary representing the Dash component ID.

    Returns:
        str: A string representation of the ID, formatted as 'component_type.component_id'.
    """
    if isinstance(id, str):
        return id
    if not isinstance(id, dict):
        raise ValueError("ID must be a dictionary.")
    return json.dumps(id, sort_keys=True, separators=(',', ':'))

def to_time_ago_string(previous_date: datetime):
    """
    Converts a flat datetime object in the past to a human-readable 'time ago' string.

    Args:
        previous_date (datetime): The datetime object to convert.

    Returns:
        str: A human-readable 'time ago' string.
    """
    now = datetime.now(ZoneInfo(TIMEZONE))
    delta = now - previous_date

    if delta.days > 0:
        return f"{delta.days} days ago"
    if delta.seconds > 3600:
        return f"{delta.seconds // 3600} hours ago"
    if delta.seconds > 60:
        return f"{delta.seconds // 60} minutes ago"
    return "Just now"
