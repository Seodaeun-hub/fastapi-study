from fastapi import FastAPI, Form, status
from fastapi.responses import (
    JSONResponse,
    HTMLResponse,
    RedirectResponse
)
from pydantic import BaseModel

app = FastAPI()

#response_class는 default가 JSONResponse. response_class가 HTMLResponse일 경우 아래 코드는?


#JSONResponse 안에 dictionary로 넣어주면 json으로 알아서 내려간다.
@app.get("/resp_json/{item_id}", response_class=JSONResponse)
async def response_json(item_id: int, q: str | None = None):
    return JSONResponse(content={
        "message":"Hello World",
        "item_id": item_id,
        "q":q}, 
        status_code=status.HTTP_200_OK)





# HTML Response
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


# Redirect(Get -> Get)
@app.get("/redirect")
async def redirect_only(comment: str | None = None):
    print(f"redirect {comment}")
    
    return RedirectResponse(url=f"/resp_html/3?item_name={comment}")
#위에 html로 다시 보내게 된다.
#redirect는 url(기본 인자값)로 던지게 된다.


# Redirect(Post -> Get)
# 이 경우가 더 많음.
# 로그인할 경우 LOGIN PAGE(POST)->MAIN PAGE(GET)
# METHOD가 바뀔 때는 302가 사용 (POST->GET) (예전부터 그렇게 쓰임)
# GET으로 바꿀 때는 302가 아니라 명세서에는 303으로 명시되어있다.
@app.post("/create_redirect")
async def create_item(item_id: int = Form(), item_name: str = Form()):
    print(f"item_id: {item_id} item name: {item_name}")

    return RedirectResponse(url=f"/resp_html/{item_id}?item_name={item_name}"
                            ,status_code=status.HTTP_302_FOUND)


#response_model은 정해진 것이다. 
class Item(BaseModel):
    name: str
    description: str
    price: float
    tax: float | None = None

# Pydantic model for response data
class ItemResp(BaseModel):
    name: str
    description: str
    price_with_tax: float
#세 개의 속성이 반드시 있어야한다.

# reponse_model
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

#return item으로 한다면 validation error가 나온다. price_with_tax가 없기 때문에
