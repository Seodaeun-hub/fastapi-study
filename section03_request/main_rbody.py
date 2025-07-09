from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional, Annotated

app = FastAPI()

#Pydantic Model 클래스는 반드시 BaseModel을 상속받아 생성. 
class Item(BaseModel):
    name:str
    description:str | None = None
    #description: Optional[str] = None
    price : float
    tax : float | None = None
    #tax: Optional[float] = None
#json 형식으로 입력될 때 인자 값들이 모두 같아야 오류가 발생하지 않는다.
    

#수행 함수의 인자로 Pydantic model이 입력되면 Json 형태의 Request Body 처리
@app.post("/items")
async def create_item(item: Item):
    print("##### item type:", type(item))
    print("##### item:",item)
    return item
#객체를 return하면 이때도 json 형식으로 나타난다.


# Request Body의 Pydantic model 값을 Access하여 로직 처리
@app.post("/items_tax/")
async def create_item_tax(item: Item):
    item_dict = item.model_dump()
    print("#### item_dict:",item_dict)
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax" : price_with_tax})

    return item_dict
#pydantic model -> dict -> json
#none -> none -> null

# Path, Query, Request Body 모두 함께 적용. 
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    
    if q:
        result.update({"q": q})
    print("#### result:", result)
    return result

class User(BaseModel):
    username: str
    full_name : str | None = None
    #full_name: Optional[str] = None


# 여러개의 request body parameter 처리. 
# json 데이터의 이름값과 수행함수의 인자명이 같아야 함.-> 여러개를 할때는 인자명이 다 같아야 함.
@app.put("/items_mt/{item_id}")
async def update_item_mt(item_id: int, item: Item, user : User):
    results = {"item_id:":item_id, "item:":item, "user:":user}
    return results

