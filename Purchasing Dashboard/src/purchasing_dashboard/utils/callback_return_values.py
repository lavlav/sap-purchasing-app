
from dash import no_update

def no_update_list(length: int):
    """
    Returns a list of `no_update` repeated `length` times.
    """
    return [no_update] * length

def no_update_tuple(length: int):
    """
    Returns a tuple of `no_update` repeated `length` times.
    """
    return tuple(no_update for _ in range(length))