import pandas
from pydantic import BaseModel, field_serializer, Field, field_validator

class CustomerDistribution(BaseModel):
    model_config = {
        "title": "CustomerDistribution",
        "description": "Response model for customer breakdown data for specific items.",
        "json_schema_extra": {
            "example": {
                "item_ids": ("ITEM123",),
                "customer_data": [
                    {"AccountType": "Retail", "Units": 100, "Sales": 5000.0},
                    {"AccountType": "Wholesale", "Units": 50, "Sales": 2500.0}
                ],
                "total_units": 150,
                "total_sales": 7500.0
            }
        },
        "arbitrary_types_allowed": True
    }

    item_ids: list[str] = Field(max_length=20, min_length=1)
    customer_data: pandas.DataFrame
    total_units: int
    total_sales: float
    calculated_at: float

    @field_serializer("item_ids")
    def serialize_item_ids(self, item_ids: list[str], _):
        return tuple(item_ids)

    @field_serializer("customer_data")
    def serialize_customer_data(self, df: pandas.DataFrame, _):
        return df.to_dict(orient="records")
    
    @field_validator("customer_data", mode="before")
    def validate_customer_data(cls, df):
        # If it's already a DataFrame, return as-is
        if isinstance(df, pandas.DataFrame):
            return df
        # Otherwise, try to build from a dict/list
        return pandas.DataFrame.from_dict(df)
