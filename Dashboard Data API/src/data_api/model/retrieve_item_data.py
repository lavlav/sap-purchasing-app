from typing import ClassVar
from pydantic import BaseModel
from pydantic import field_validator, ValidationInfo
from data_api.utils.type_aliases import ItemId

class RetrieveItemDataRequest(BaseModel):
    """
    Request model for retrieving order history via POST.
    """
    item_ids: list[ItemId] = []

    
    