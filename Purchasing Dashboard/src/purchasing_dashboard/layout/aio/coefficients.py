from typing import Literal, TypedDict

from purchasing_dashboard.utils.info_messages import best_fit_equation_markdown_template


class Coefficients(TypedDict):
    slope: float | Literal["m"]
    intercept: float | Literal["b"]

    DEFAULT = {
        "slope": "m",
        "intercept": "b"
    }


def format_markdown_template(coefficients: Coefficients) -> str:
    slope = coefficients["slope"]
    intercept = coefficients["intercept"]
    binoperator = "+"
    if type(slope) is float:
        slope = f"{slope:.4f}".rstrip('0').rstrip('.')
    if type(intercept) is float:
        binoperator = "-" if intercept < 0 else "+"
        intercept = abs(intercept)
        intercept = f"{intercept:.4f}".rstrip('0').rstrip('.')
    return best_fit_equation_markdown_template \
        .replace("{slope}", str(slope)) \
        .replace("{intercept}", str(intercept)) \
        .replace("{plus_or_minus}", binoperator)