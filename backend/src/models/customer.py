from pydantic import BaseModel, ConfigDict, Field

class Customer(BaseModel):
    customer_id: str = Field(min_length=1)
    customer_unique_id: str = Field(min_length=1)
    customer_zip_code_prefix: int
    customer_city: str = Field(min_length=1)
    customer_state: str = Field(min_length=2, max_length=2)

    model_config = ConfigDict(str_strip_whitespace=True)