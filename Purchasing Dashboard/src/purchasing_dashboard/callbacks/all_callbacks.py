# pyright: ignore
from purchasing_dashboard.callbacks import (
    common_callbacks,
    item_forecast_callbacks,
    item_history_callbacks,
    pir_download_callbacks,
    customer_breakdown_callbacks,
    usage_table_callbacks,
    demand_summary_plot_callbacks,
    vendor_snapshot_callbacks,
    saved_itemsets_callbacks,
    projected_coverage_callbacks,
    price_point_analysis_callbacks,
    retail_buildout_callbacks
)
from purchasing_dashboard.utils.environment_variables import DEBUG_ENABLED
if DEBUG_ENABLED:
    from purchasing_dashboard.callbacks import test_error_callbacks