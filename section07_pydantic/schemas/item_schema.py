from pydantic import ValidationError, BaseModel,model_validator,Field
from fastapi import Form
from typing import Annotated
from fastapi.exceptions import RequestValidationError

class Item(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(None, max_length=500)
    price: float = Field(..., ge=0)
    tax: float = None

    @model_validator(mode='after')
    def tax_must_be_less_than_price(cls, values):
        price = values.price
        tax = values.tax
        if tax > price:
            raise ValueError("Tax must be less then price")

        return values
    
def parse_user_form(
    name: str = Form(..., min_length=2, max_length=50),
    description: Annotated[str, Form(max_length=500)] = None,
    price: float = Form(..., ge=0),
    tax: Annotated[float, Form()] = None, 
) -> Item:
    try: 
        item = Item(
            name = name,
            description = description,
            price = price, 
            tax = tax
        )

        return item
    except ValidationError as e:
        raise RequestValidationError(e.errors()) 