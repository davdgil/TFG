from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderFinalItem(BaseModel):
    product_id: str = Field(min_length=1)
    price: float
    freight_value: float
    product_category_name_english: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class OrderFinal(BaseModel):
    order_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    order_date: datetime
    items: list[OrderFinalItem]

    model_config = ConfigDict(str_strip_whitespace=True)
