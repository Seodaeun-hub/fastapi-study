# Section 04 - Response 실습 요약

# 학습 주제
- FastAPI에서 다양한 방식으로 **응답을 반환하는 방법**
- 'JSON Response', 'HTML Response', 'Redirect Response', 'response_model'

# 주요 개념 요약
# 1. JSON Response
```python
from fastapi import FastAPI, Form, status
from fastapi.responses import JSONResponse
app = FastAPI()

@app.get("/resp_json/{item_id}", response_class=JSONResponse)
async def response_json(item_id: int, q: str | None = None):
    return JSONResponse(content={
        "message":"Hello World",
        "item_id": item_id,
        "q":q}, 
        status_code=status.HTTP_200_OK)
```
- JSON Response를 사용할 때는 from fastapi.responses import JSONResponse로 불러오기
- response_class=JSONResponse를 쓰지 않아도 default가 JSONResponse이기 때문에 json 형태로 불러오지만 swagger에는 나타나지않으므로 보기 좋게 하기 위해 명시한다.
- JSONResponse 안에 dictionary로 넣어주면 json으로 알아서 내려간다.
- status_code를 지정할 수 있다. (status를 쓸 경우 improt status 사용)

# 2. HTML Response
```python
from fastapi import FastAPI, Form, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

@app.get("/resp_html/{item_id}", response_class=HTMLResponse)
async def response_html(item_id: int, item_name: str | None = None):
    html_str = f'''
    <html>
    <body>
        <h2>HTML Response</h2>
        <p>item_id: {item_id}</p>
        <p>item_name: {item_name}</p>
    </body>
    </html>
    '''
    return HTMLResponse(html_str, status_code=status.HTTP_200_OK)
```
- html도 마찬가지로 response_class=HTMLResponse를 사용하지 않아도 html로 적용되지만 swagger UI에서 나타나게 하기 위해 사용한다.
- html 안 {}에 받아들인 인자들이 들어가게 된다.

# 3.Redirect Response
**Redirect (Get -> Get)**
```python
@app.get("/redirect")
async def redirect_only(comment: str | None = None):
    print(f"redirect {comment}")
    
    return RedirectResponse(url=f"/resp_html/3?item_name={comment}")
```
- Redirect Response는 url(기본 인자값)으로 던지게 된다.
- 여기서는 위에 resp_html로 보내게 된다. item_name에 comment가 들어가게 된다.

**Redirect (Post -> Get)**
```python
@app.post("/create_redirect")
async def create_item(item_id: int = Form(), item_name: str = Form()):
    print(f"item_id: {item_id} item name: {item_name}")

    return RedirectResponse(url=f"/resp_html/{item_id}?item_name={item_name}" ,status_code=status.HTTP_302_FOUND)
```
- Redirect는 Post -> Get의 경우가 더 많다.
- 로그인할 경우 LOGIN PAGE(POST)->MAIN PAGE(GET)
- **주의사항** METHOD가 바귈 때는 302를 예전부터 많이 사용되었지만 GET으로 바꿀 때는 303을 사용해야한다.

# 4. Response_model
```python
class Item(BaseModel):
    name: str
    description: str
    price: float
    tax: float | None = None

class ItemResp(BaseModel):
    name: str
    description: str
    price_with_tax: float

@app.post("/create_item" ,response_model=ItemResp,
          status_code=status.HTTP_201_CREATED)
async def create_item_model(item: Item):
    if item.tax :
        price_with_tax = item.price + item.tax
    else :
        price_with_tax = item.price
    item_resp = ItemResp(name=item.name,
             description=item.description,
             price_with_tax=price_with_tax)

    return item_resp
```
- return 할 때 반드시 response_model로 명시된 것으로 나와야한다.
- 즉 위에 response와 달리 반드시 response_model이 정해져야한다.
- 또한 response_model에 정의된 속성들은 반드시 있어야한다.
