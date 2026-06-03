from datetime import datetime
from enum import Enum
from typing import ClassVar, Set, Optional, Any
import pandas as pd
from pydantic import BaseModel, Field, field_validator
import json
import logging

from dashboard_common.model.time_bucket import TimeBucket

logger = logging.getLogger(__name__)

class ForecastType(Enum):
    auto = "auto", "Automatic", 1
    """
    Let the backend choose the best model.
    """
    basic = "basic", "Basic Regression", 2
    """
    Use simple 2D linear regression.
    """
    linear = "linear", "Linear Regression", 3
    """
    Use linear regression with time series feature augmentation.
    """
    vendored = "vendored", "Advanced Regression", 4
    """
    Use The Forecasting Company's API.
    """
    boosted_tree = "boosted_tree", "Boosted Tree", 5
    """
    Use XGBoost with time series feature augmentation.
    """
    def __init__(self, value, display_name, order):
        # logger.debug(f"Creating ForecastType: {value}, {display_name}, {order}")
        self._value_ = value
        self.display_name = display_name
        self.order = order

    def get_display_name(self):
        return self.display_name

    def __str__(self):
        return self._value_

class Forecast(BaseModel):
    item_codes: frozenset[str]
    initiated_type: ForecastType = ForecastType.auto
    received_type: ForecastType
    num_forecasted_points: int
    time_bucket: TimeBucket
    time_initiated: datetime
    time_computed: datetime
    goodness_of_fit: dict[str, float]  # RMSE or similar metrics
    forecast_data: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True
        frozen = True  # enable hashing

    COLUMN_ALIASES: ClassVar[dict[str, set[str]]] = {
        "Units": {"units", "forecast", "value"},
        "Time": {"time", "timestamp", "date", "orderdate"}
    }

    @field_validator("item_codes", mode="before")
    def coerce_item_codes_to_frozenset(cls, v):
        if type(v) is str:
            logger.warning(f"Expected a collection of item codes, got a single string: {v}.")
            v = [v]
        if type(v) is list or type(v) is set:
            return frozenset(v)
        if type(v) is frozenset:
            return v
        raise TypeError(f"Expected frozenset, set, or list for item_codes, got {type(v)}")

    @field_validator("received_type")
    def validate_received_type(cls, v):
        # Can't receive an "auto" forecast
        if v == ForecastType.auto: 
            raise ValueError("Received forecast type cannot be 'auto'.")
        return v

    @field_validator("forecast_data", mode="before")
    def coerce_to_dataframe(cls, v):
        if not isinstance(v, pd.DataFrame):
            try:
                v = pd.DataFrame(v)
            except Exception as e:
                raise ValueError(f"Could not convert input to DataFrame: {e}")
        return v

    @field_validator("forecast_data")
    def validate_forecast_data(cls, df: pd.DataFrame) -> pd.DataFrame:
        renamed = {}
        for canonical, aliases in cls.COLUMN_ALIASES.items():
            match = next(((col, col.lower())
                         for col in df.columns if col.lower() in aliases), None)
            if not match:
                raise ValueError(
                    f"Missing required column for '{canonical}'. Accepted aliases: {aliases}")
            col, matched_alias = match
            if col != canonical:
                logger.warning(
                    f"Column '{col}' matched alias '{matched_alias}' and was renamed to '{canonical}'. "
                    f"Consider using '{canonical}' directly for clarity."
                )
            renamed[col] = canonical

        df = df.rename(columns=renamed)

        if not pd.api.types.is_numeric_dtype(df["Units"]):
            raise ValueError("The 'Units' column must be numeric.")
        if pd.api.types.is_numeric_dtype(df["Time"]):
            logger.warning(
                "The 'Time' column is numeric, converting to datetime. "
                "Ensure this is intended as it may lead to unexpected behavior."
            )
            df["Time"] = pd.to_datetime(df["Time"], unit="s", errors="coerce")
        elif not pd.api.types.is_datetime64_any_dtype(df["Time"]):
            logger.debug(f"Time column: {df['Time'].head()}")
            raise ValueError(
                f"The 'Time' column must be datetime or timestamp. Got {df['Time'].dtype} instead.")

        return df

    def __hash__(self):
        return hash((self.item_codes, self.time_bucket))

    def __eq__(self, other: Any):
        return isinstance(other, Forecast) and (
            self.item_codes == other.item_codes and
            self.time_bucket == other.time_bucket
        )

    def to_dict(self) -> dict:
        # Convert datetime to int for JSON serialization
        self.forecast_data["Time"] = self.forecast_data["Time"].astype(
            int) // 10**9
        return {
            "item_codes": list(self.item_codes),
            "initiated_type": self.initiated_type.value,
            "received_type": self.received_type.value,
            "num_forecasted_points": self.num_forecasted_points,
            "time_bucket": self.time_bucket,
            "time_initiated": self.time_initiated.isoformat(),
            "time_computed": self.time_computed.isoformat(),
            "goodness_of_fit": self.goodness_of_fit,
            "forecast_data": self.forecast_data.to_dict(orient="records"),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Forecast":
        df = pd.DataFrame(data["forecast_data"])
        df["Time"] = pd.to_datetime(df["Time"], unit="s", errors="coerce")
        return cls(
            item_codes=frozenset(data["item_codes"]),
            initiated_type=ForecastType[data["initiated_type"]],
            received_type=ForecastType[data["received_type"]],
            num_forecasted_points=data["num_forecasted_points"],
            time_bucket=TimeBucket(data["time_bucket"]),
            time_initiated=datetime.fromisoformat(data["time_initiated"]),
            time_computed=datetime.fromisoformat(data["time_computed"]),
            goodness_of_fit=data["goodness_of_fit"],
            forecast_data=df,
        )


class ForecastSet(BaseModel):
    forecasts: Set[Forecast] = Field(default_factory=set)

    def get(self, item_codes: frozenset[str], time_bucket: TimeBucket) -> Optional[Forecast]:
        if(type(item_codes) is not frozenset):
            if type(item_codes) is str:
                logger.warning(f"Expected a collection of item codes, got a single string: {item_codes}.")
                item_codes = [item_codes]
            elif (type(item_codes) is not set and
                  type(item_codes) is not list):
                raise TypeError(
                    f"Expected frozenset, set, or list for item_codes, got {type(item_codes)}")
            logger.warning(f"Coercing {item_codes} to frozenset.")
            item_codes = frozenset(item_codes)
        return next(
            (f for f in self.forecasts if f.item_codes == item_codes and f.time_bucket == time_bucket),
            None
        )

    def put(self, new_forecast: Forecast):
        existing = self.get(new_forecast.item_codes, new_forecast.time_bucket)
        if existing:
            if new_forecast.time_initiated < existing.time_initiated:
                raise ValueError(
                    f"Existing forecast for ({new_forecast.item_codes}, {new_forecast.time_bucket}) "
                    f"is newer (initiated {existing.time_initiated})."
                )
            self.forecasts.remove(existing)
        self.forecasts.add(new_forecast)

    def to_dict(self) -> dict:
        return {
            "forecasts": [f.to_dict() for f in self.forecasts]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastSet":
        return cls(
            forecasts={Forecast.from_dict(f)
                       for f in data.get("forecasts", [])}
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ForecastSet":
        return cls.from_dict(json.loads(json_str))
