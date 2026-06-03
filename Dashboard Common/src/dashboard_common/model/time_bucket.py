from datetime import datetime, timedelta
from enum import Enum

class TimeBucket(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"

    

    def get_resample_rule(self) -> str:
        """
        Returns the resample rule/frequency string, for use in e.g. `pandas.DataFrame.resample()`_.

        .. _pandas.DataFrame.resample(): https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
        """
        resample_rules: dict[str, str] = {
            "day": "D",
            "week": "W",
            "month": "MS",
            "quarter": "QS",
            "year": "YS"
        }
        return resample_rules.get(self.value)

    def get_start(self, date: datetime = None) -> datetime:
        """
        Returns the start of the time bucket that contains the given date.
        """
        date.replace(hour=0, minute=0, second=0, microsecond=0)
        match self.value:
            case "day":
                current_period_start = date
            case "week":
                current_period_start = date - timedelta(date.weekday())
            case "month":
                current_period_start = date.replace(day=1)
            case "quarter":
                current_period_start = datetime(
                    date.year, 3 * ((date.month - 1) // 3) + 1, 1)
            case "year":
                current_period_start = date.replace(day=1, month=1)
            case _:
                raise ValueError(f"Unknown time interval {time_bucket}")
        return current_period_start
