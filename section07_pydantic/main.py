from fastapi import FastAPI, Path, Query, Form, Depends
from pydantic import BaseModel, Field, model_validator
from typing import Annotated
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
from schemas.item_schema import Item,parse_user_form
app = FastAPI()

    
@app.put("/items/{item_id}")
async def update_item(item_id: int, q: str, item: Item=None):
#async def update_item(item_id: int = Path(...), q: str = Query(...), item: Item=None):
#사실 이렇게 명시해주는게 정확하다.
    return {"item_id": item_id, "q": q, "item": item}

# Path, Query, Request Body(json)
@app.put("/items_json/{item_id}") #여기서는 반드시 Path(...), Query() 반드시 써줘야 함.
async def updata_item_json(
    item_id:int = Path(..., gt=0),
    q1: str = Query(None, max_length=50),
    #q1: Annotated[str, Query(max_length=50)] = None
    q2: str = Query(None, min_length=3),
    #q2: Annotated[str, Query(min_length=3)] = None
    item: Item = None
):
    return {"item_id":item_id, "q1":q1,"q2":q2,"item":item}

# Path, Query, Form
#Form을 쓸 경우는 개별 필드 하나당 하나씩 Form 필드 안에 조건을 써준다.
#여기서는 개별필드이기때문에 tax가 price보다 크다 이런건 할 수 없다.
@app.post("/items_form/{item_id}")
async def update_item_form(
    item_id: int = Path(..., gt=0, title="The ID of the item to get"),
    q: str = Query(None, max_length=50),
    name: str = Form(..., min_length=2, max_length=50),
    description: Annotated[str, Form(max_length=500)] = None,
    #description: str = Form(None, max_length=500),
    price: float = Form(..., ge=0), 
    tax: Annotated[float, Form()] = None
    #tax: float = Form(None)
):
    return {"item_id": item_id, "q": q, "name": name, 
            "description": description, "price": price, "tax": tax}

# Path, Query, Form을 @model_validator 적용. 
@app.post("/items_form_01/{item_id}")
async def update_item_form_01(
    item_id: int = Path(..., gt=0, title="The ID of the item to get"),
    q: str = Query(None, max_length=50),
    name: str = Form(..., min_length=2, max_length=50),
    description: Annotated[str, Form(max_length=500)] = None,
    #description: str = Form(None, max_length=500),
    price: float = Form(..., ge=0), 
    tax: Annotated[float, Form()] = None
    #tax: float = Form(None)
):
    #인자를 받고 안에서 검증을 시키게된다. 생성이 될 때 검증을 한다.
    try:
        item = Item(name=name, description=description, price=price, tax=tax)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    return item


@app.post("/items_form_02/{item_id}")
async def update_item_form_02(
    item_id: int = Path(..., gt=0, title="The ID of the item to get"),
    q: str = Query(None, max_length=50),
    item: Item = Depends(parse_user_form)
):
    return {"item_id": item_id, "q": q, "item": item}

#Depends() : fastapi에게 불러서 명확하게 넣어줘야한다라는 것을 알리기 위해. 함수 같은것이 들어감.