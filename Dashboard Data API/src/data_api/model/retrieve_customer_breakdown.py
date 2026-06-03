

from dataclasses import field
from datetime import datetime, timedelta
from typing import Optional

from pydantic import ValidationInfo, field_serializer, field_validator
from data_api.model.retrieve_item_data import RetrieveItemDataRequest
from dashboard_common.model.time_bucket import TimeBucket


class RetrieveCustomerBreakdownRequest(RetrieveItemDataRequest):
    """
    Request model for retrieving customer breakdown via POST.
    """
    until: Optional[datetime] = None
    average_by: Optional[TimeBucket] = None

    @field_validator("until", mode="before")
    def validate_until(cls, v: datetime | float | None, info: ValidationInfo):
        if isinstance(v, float):
            return datetime.fromtimestamp(v)
        return v

    @field_serializer("until")
    def serialize_until(self, v: Optional[datetime], info: ValidationInfo) -> float:
        return v.timestamp() if v else 0.0