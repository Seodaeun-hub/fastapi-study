# Section 03 - Request 실습 요약

# 학습 주제
- 클라이언트로부터 들어오는 요청(Request) 데이터 처리 방법
- Path Parameter, Query Parameter, Request Body,Form

## 주요 개념 요약
# 1. Path Parameter (경로 변수)
```python
app = FastAPI()
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
@app.get("/items/all")
async def read_all_items():
    return {"message": "all items"}
```
-> URL 경로 자체에 포함된 값 예 : /localhost:8081/3
-> 타입 힌트를 넣으면 자동으로 검증됨(pydantic에서 검증되는 것.)
-> **주의사항** : 순차적으로 path를 찾기 때문에 위에꺼가 매핑이 되므로 items/all로 된다면 오류가 발생한다. 고정된 값을 사용할 때는 반드시 맨 위로 올려야한다. 그러므로 /items/all이 맨 위로 가야한다.

# 2. Query Parameter (쿼리 문자열)
```python
#path, query 함께 사용한 예시
from fastapi import FastAPI
from typing import Optional
app = FastAPI()
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None): 
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```
-> item_id 까지는 path parameter
-> q는 query parameter
-> URL ? 이후에 오는 key=value 형태
-> **주의사항** : default 값이 설정되어있지않다면 반드시 적어주어야 오류가 나지 않음. 
-> q: str | None = None 아니면 q:Opitional[str]=None 은 적어주지않는다면 None 값으로 받아들여서 오류가 발생하지 않음.

# 3.Request Body (JSON 데이터)
```python
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional, Annotated
app = FastAPI()
class Item(BaseModel):
    name:str
    description:str | None = None
    price : float
    tax : float | None = None
@app.post("/items")
async def create_item(item: Item):
    return item
```
-> Pydantic Model 클래스는 반드시 BaseModel을 상속받아 생성.
-> 불러올 json 형태의 인자들과 같아야 오류 발생하지 않음.
-> 객체를 return하면 이때도 json 형식으로 나타난다.

```python
@app.post("/items_tax/")
async def create_item_tax(item: Item):
    item_dict = item.model_dump()
    print("#### item_dict:",item_dict)
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax" : price_with_tax})

    return item_dict
```
-> item.model_dump()는 pydantic 모델(Item) 인스턴스를 dict(딕셔너리)로 변환하는 메서드야.
-> 여기서 model_dump()를 사용한 이유는 추가 데이터를 dict.update()로 넣기 위해서 이다.
-> pydantic 객체(item)은 그냥 dict처럼 수정이 불가능하다. 그러므로 dict 형태로 변환한 후에야 값 추가/수정 가능하다.

-> 여러개의 request body parameter 처리. json 데이터의 이름값과 수행함수의 인자명이 같아야 함.-> 여러개를 할때는 인자명이 다 같아야 함.

# 4. Form 
```python
from pydantic import BaseModel
from typing import Optional, Annotated
from fastapi import FastAPI, Form

app = FastAPI()
@app.post("/login")
async def login(username: str= Form(),
                email: str=Form(),
                country: str=Form(None)):
    return {"username:":username,
            "email:":email,
            "country:":country}
```
-> FastAPI에서 Form 데이터를 받으려면 Form 클래스를 명시적으로 써줘야한다.
-> 개별 Form data 값을 Form()에서 처리하여 수행함수 적용.
-> Form()은 form data값이 반드시 입력되어야 함. Form(None)과 Annotated[str, Form()] = None은 Optional
-> **Content-Type은 application/x-222-form-urlencoded로 설정됨.**
-> Swagger UI에서 JSON 대신 form 필드로 입력창 전환됨.

**Request Body 와 Form의 차이**
1. Request Body(JSON)은 대부분의 API 클라이언트가 사용하는 방식. 예시로 Postman, React, 앱 등이 있다.
2. Form Data는 HTML <form> 태그로 전송된 데이터. 예시로 웹 브라우저에서 로그인/회원가입 등

```python
# json request body용 end point
@app.post("/items_json/")
async def create_item_json(item: Item):
    return item

# form tag용 end point
@app.post("/items_form/")
async def create_item_json(name: str = Form(),
    description: Annotated[str, Form()] = None,
    price: str = Form(),
    tax: Annotated[int, Form()] = None
    ):
    return {"name": name, "description": description, "price": price, "tax": tax}
```


