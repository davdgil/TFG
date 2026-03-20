from pydantic import BaseModel, ConfigDict, Field


class OrderItem(BaseModel):
    order_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    price: float
    freight_value: float
    product_category_name_english: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)
