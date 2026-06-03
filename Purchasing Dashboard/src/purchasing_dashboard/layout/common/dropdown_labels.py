from dash import html

from purchasing_dashboard.utils.string_manipulation import truncate_string

def generate_option_label(shorthand_code, full_name, max_length=20, missing_full_name_placeholder="info"):
    """
    Generate a label for an option in a dropdown, to be used to populate its `options` property.

    Args:
        shorthand_code (str): The shorthand code of the option, to be displayed prominently.
        full_name (str): The full name of the item, which might be truncated in the dropdown option.
        max_length (int): The maximum length of the full name to display. Defaults to 20, which
        typically fits dropdowns placed on a sidebar.

    Returns:
        dict: A dictionary containing the label, value, and search fields for the option.
    """
    full_name_truncated = truncate_string(full_name, max_length, space_lookback=6)
    if full_name_truncated == "":
        label_suffix = f" (No {missing_full_name_placeholder} found)"
        full_name_classname = "option-name italic"
    else:
        label_suffix = f" - {full_name_truncated}"
        full_name_classname = "option-name"
    return {
            "label": html.Span(
                children=[shorthand_code, html.Span(label_suffix, className=full_name_classname)],
                className="option-label",
                title=full_name
            ),
            "value": shorthand_code,
            "search": f"{shorthand_code}{full_name}",
        }