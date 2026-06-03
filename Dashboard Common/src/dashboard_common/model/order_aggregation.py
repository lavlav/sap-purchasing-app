

from datetime import datetime
import pandas
from pydantic import BaseModel

from dashboard_common.model.time_bucket import TimeBucket
from pydantic import field_validator, ValidationError


class OrderAggregation(BaseModel):
    """
    Represents order dataframes, aggregated by time bucket.
    """
    data: dict[TimeBucket, pandas.DataFrame] = {}
    item_codes: frozenset[str] = frozenset()
    time_initiated: datetime
    time_computed: datetime

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an OrderAggregation instance from a dictionary.
        """
        historical_data = {}
        for key, value in data.get("data", {}).items():
            dataframe = pandas.DataFrame(value)
            dataframe["OrderDate"] = pandas.to_datetime(dataframe["OrderDate"])
            historical_data[TimeBucket[key]] = dataframe
        return cls(
            data=historical_data,
            item_codes=frozenset(data.get("item_codes", [])),
            time_initiated=data.get("time_initiated", datetime.now()),
            time_computed=data.get("time_computed", datetime.now())
        )

    def to_dict(self) -> dict:
        """
        Convert the OrderAggregation instance to a dictionary.
        """
        return {
            "data": {k.value: v.to_dict(orient="records") for k, v in self.data.items()},
            "item_codes": list(self.item_codes),
            "time_initiated": self.time_initiated,
            "time_computed": self.time_computed
        }
    
    def __hash__(self):
        return hash(self.item_codes, frozenset(self.data.keys()))
    
    @field_validator("data", mode="before")
    def validate_data_keys(cls, v):
        if not isinstance(v, dict):
            raise TypeError("data must be a dictionary")
        invalid_keys = [k for k in v.keys() if not isinstance(k, TimeBucket)]
        if invalid_keys:
            raise ValidationError(f"All keys in 'data' must be TimeBuckets. Invalid keys: {invalid_keys}")
        return v
