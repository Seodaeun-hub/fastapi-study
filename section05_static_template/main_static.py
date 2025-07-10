from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


from fastapi.templating import Jinja2Templates

app = FastAPI()
# /static은 url path, StaticFiles의 directory는 directory명, name은 url_for등에서 참조하는 이름 
app.mount("/static", StaticFiles(directory="static"), name="static")
#path가 /static이면 StaticFiles로 권한을 넘긴다.
#path랑 directory 이름은 같게 하는것이 기본적이다.

# jinja2 Template 생성. 인자로 directory 입력
templates = Jinja2Templates(directory="templates")

@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str, q: str | None = None):
    html_name = "item_static.html"
    #html_name = "item_urlfor.html"
    return templates.TemplateResponse(
        request=request, name=html_name, context={"id": id, "q_str": q}
    )
 