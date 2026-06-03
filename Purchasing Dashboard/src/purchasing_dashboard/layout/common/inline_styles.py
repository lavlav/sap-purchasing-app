

INLINE_ITEM_HISTORY_TABLE_CELL_STYLE = {
    "white-space": "normal",
    "textAlign": "left",
}

STRIPED_DATATABLE_STYLE_DATA_CONDITIONAL = [
    {
        "if": {"row_index": "odd"},
        "backgroundColor": "#f2f2f2",
    },
    {
        "if": {"row_index": "even"},
        "backgroundColor": "#ffffff",
    },
]

GRAY_OUT_EXCLUDED_STYLE_DATA_CONDITIONAL = [
    {
        "if": {
            "filter_query": "{Include} = 'false'",
        },
        "color": "lightgray",
        "backgroundColor": "dimgray",
        "textDecoration": "line-through",
    }
]

FORECASTED_USAGE_TABLE_ENTRY_STYLE = "red"