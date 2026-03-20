from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    product_id: str = Field(min_length=1)
    product_category_name_english: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)
