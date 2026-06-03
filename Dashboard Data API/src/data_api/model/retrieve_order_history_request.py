

from typing import ClassVar
from pydantic import ValidationInfo, field_validator
from data_api.model.retrieve_item_data import RetrieveItemDataRequest


class RetrieveOrderHistoryRequest(RetrieveItemDataRequest):
    """
    Request model for retrieving order history.
    """
    def __init__(self, item_ids, time_bucket=None):
        super().__init__(item_ids=item_ids)
        self.time_bucket = time_bucket

    def to_dict(self):
        return {
            "item_ids": self.item_ids,
            "time_bucket": self.time_bucket
        }
    
    MAX_IDS: ClassVar[int] = 25 # Chosen arbitrarily

    @field_validator('item_ids')
    def validate_item_ids(cls, v: list[str], info: ValidationInfo):
        if len(v) > cls.MAX_IDS:
            raise ValueError(f"item_ids cannot contain more than {cls.MAX_IDS} items")
        return v