from pydantic import ValidationError, field_validator

from data_api.model.retrieve_item_data import RetrieveItemDataRequest
from dashboard_common.model.forecast import ForecastType
from dashboard_common.model.time_bucket import TimeBucket
from data_api.utils.logging import logger



class RetrieveForecastRequest(RetrieveItemDataRequest):
    """
    Request model for retrieving forecasts for multiple items.
    """
    model_config = {
        "use_enum_values": True
    }
    
    time_bucket: TimeBucket = "month"
    n_forecasts: int = 1
    forecast_type: ForecastType = "auto"

    def __init__(self, item_ids=None, time_bucket=None, n_forecasts=1, forecast_type="auto"):
        super().__init__(item_ids=item_ids)
        self.time_bucket = time_bucket
        self.n_forecasts = n_forecasts
        self.forecast_type = forecast_type

    @field_validator("forecast_type", mode="before")
    def validate_forecast_type(cls, value):
        if not isinstance(value, ForecastType):
            raise ValidationError(f"Invalid forecast type: {value}")
        if value not in ForecastType.__members__.values():
            raise ValidationError(f"Unsupported forecast type: {value}")
        return value