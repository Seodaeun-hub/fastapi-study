# Section 05 - Static File & Template 실습 요약

# 학습 주제
- FastAPI에서 **템플릿 엔진(Jinja2)**를 사용해 HTML 페이지 렌더링하는 방법
- 템플릿에서 **변수 전달**, **조건문(if)**, **반복문(for)**, **HTML 안전 처리(|safe)** 등 사용법
- **템플릿과 Request 객체의 연결 방식** 이해 및 실습
- FastAPI에서 `/static` 경로로 **정적 파일(CSS, JS, 이미지 등)**을 제공하는 방법
- `StaticFiles` 클래스를 활용하여 **정적 파일 요청 처리 권한을 위임하는 구조** 이해

# 주요 개념 요약

# 1. Jinja2 기본 사용해보기
```python
# item.html
<html>
<head>
    <title>Item Details</title>
</head>
<body>
    <h1>Item id: {{ id }}</h1>
    <h1>query: {{ q_str }}</h1>
    <h3>{{ item }}</h3>
    <h5>item name : {{ item.name }}, item price : {{ item.price }}</h5>
    <p>item_dict[name]: {{ item_dict['name'] }}</p>
</body>
</html>

#main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

templates=Jinja2Templates(directory="templates")

class Item(BaseModel):
    name: str
    price: float

@app.get("/items/{id}",response_class=HTMLResponse)
async def read_item(request: Request, id: str, q: str | None= None) :
    item = Item(name="test_item",price=10)
    item_dict = item.model_dump()

    return templates.TemplateResponse(
        request=request,
        name="item.html",
        context={"id":id, "q_str":q, "item":item, "item_dict":item_dict}
    )
```
- jinja2 Template 생성할 때 인자로 directory 입력.
- templates=Jinja2Templates(directory="templates")
- **template engine을 사용할 경우 반드시 Request 객체가 인자로 입력되어야 함.**, request: Request
- return의 순서
1. request=request
2. name="item.html"
3. context={}
- context 안에 있는 내용을 html에 보내는 것이다.
- **주의사항** : 이때 key 값이 전달이 되므로 key값을 html과 맞춰야 한다.

# Jinja2 주요 구문
- {{...}} : 변수나 표현식
- {%...%} : if, for문
- {#...#} : 주석

# 2. Jinja2의 if문 사용해보기
```python
# item_gubun.html
<html>
<head>
    <title>Item Details</title>
</head>
<body>
    {% if gubun == "admin" %}
    <p>이것은 어드민용 item 입니다.</p>
    {% else %}
    <p>이것은 일반용 item 입니다.</p>
    {% endif %}
    <h3> {{item}} </h3>
</body>
</html>

# main.py
@app.get("/item_gubun",response_class=HTMLResponse)
async def read_item_by_gubun(request: Request, gubun: str):
    item = Item(name="test_item_02", price=4.0)
    
    return templates.TemplateResponse(
        request=request, 
        name="item_gubun.html", 
        context={"gubun": gubun, "item": item}
    )
```
- **if문 html의 주의사항** : 반드시 if문 마지막에 {% endif %} 써야함.

# 3. Jinja2의 for문 사용해보기
```python
# item_all.html
<html>
<head>
    <title>Item Details</title>
</head>
<body>
    {% for item in all_items %}
    <h3> item name: {{ item.name }} item price: {{ item.price }}</h3>
    {% endfor %}
</body>
</html>

#main.py
@app.get("/all_items", response_class=HTMLResponse)
async def read_all_items(request: Request):
    all_items = [Item(name="test_item_" +str(i), price=i) for i in range(5) ]
    print("all_items:", all_items)
    return templates.TemplateResponse(
        request=request, 
        name="item_all.html", 
        context={"all_items": all_items}
    )
```
- **for문 html의 주의사항** : 반드시 if문 마지막에 {% endfor %} 써야함.

# 4. HTML tag를 safe로 적용하기
```python
# read_safe.html
<html>
<body>
    <h1> 우리 상품은 </h1>
    {{ html_str | safe }}
</body>
</html>

# main.py
@app.get("/read_safe", response_class=HTMLResponse)
async def read_safe(request: Request):
    html_str = '''
    <ul>
    <li>튼튼</li>
    <li>저렴</li>
    </ul>
    '''
    return templates.TemplateResponse(
        request=request, 
        name="read_safe.html", 
        context={"html_str": html_str}
    )
```
- 이렇게 직접 태그 html을 넘겨주는 경우는 흔치 않으며 짧은 태그를 보낼 경우에 사용될 수 있다.
- {{ html_str }}로 적을 경우 html 태그 그대로 나오게 된다.
- | safe를 포함해야됨.

# 5. FastAPI에서 정적 파일(Static File) 다루는 법
```python
# item_static.html
<html>
<head>
    <title>Item Details</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <h1>Item id: {{ id }}</h1>
    <h3><a href="/static/link_tp.html">another link</a></h3>
</body>
</html>

# link_tp.html
<html>
<head>
    <title>link tp</title>
    <link rel="stylesheet" href="/static/css/styles.css">

</head>
<body>
    <h1>Another Result</h1>
</body>
</html>

# main_static.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str, q: str | None = None):
    html_name = "item_static.html"
    return templates.TemplateResponse(
        request=request, name=html_name, context={"id": id, "q_str": q}
    )
```
- **mount : /static 경로로 들어오는 요청은 FastAIP가 직접 처리하지 않고, StaticFiles 클래스에게 위임하여 해당 디렉터리 안의 파일을 그대로 서빙함.**
- directory="static" : 실제 파일이 저장된 폴더명
- name="static" : 템플릿에서 url_for("static, path="...") 사용 시 참조되는 이름

