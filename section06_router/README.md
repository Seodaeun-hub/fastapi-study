# SECTION 06 - APIRouter 실습 요약

# 학습 주제
- FastAIP에서 라우터 분리(APIRouter)를 사용하는 이유
- 모듈화된 라우팅 구성 방식 이해 및 실습
- 실제 프로젝트 구조 설계에 적용

# 핵심 개념 정리
1. APIIRouter란?
- FastAPI에서 라우팅 로직을 분리해 모듈 단위로 관리할 수 있게 하는 도구
- 메인이 복잡해지는 것을 방지하고 유지보수성을 향상시킴

```python
# 분리 되지 않은 상태
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

@app.get("/item/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/item")
async def create_item(item: Item):
    return item

@app.put("/item/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, "item": item}

@app.get("/users/")
async def read_users():
    return [{"username": "Rickie"}, {"username": "Martin"}]


@app.get("/users/me")
async def read_user_me():
    return {"username": "currentuser"}


@app.get("/users/{username}")
async def read_user(username: str):
    return {"username": username}
```
**item과 users로 분리해야겠다고 생각.**

```python
#routers/item.py
from fastapi import FastAPI,APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/item",tags=["item"])

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None
    
@router.get("/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@router.post("/")
async def create_item(item: Item):
    return item

@router.put("/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, "item": item}
```
**router = APIRouter(prefix="/item",tags=["item"])**
- **prefix="/item"** : 해당 라우터에 포함된 모든 경로 앞에 공통적으로 붙는 url 접두어.
- 예: @router.get("/{item_id}") -> 실제 호출 경로는 /item/{item_id}
- **tags=["item"]** : Swagger 문서에서 이 라우터에 속한 모든 API를 item 그룹으로 묶어줌. API 문서에서 시각적으로 보기 좋고 정리도 쉬워짐.

```python
#routers/user.py
from fastapi import FastAPI,APIRouter

router = APIRouter(prefix="/user",tags=["user"])

@router.get("/")
async def read_users():
    return [{"username": "Rickie"}, {"username": "Martin"}]


@router.get("/me")
async def read_user_me():
    return {"username": "currentuser"}


@router.get("/{username}")
async def read_user(username: str):
    return {"username": username}
```
- **item과 같은 방식으로 router 정의한다.**

```python
from fastapi import FastAPI
from routes import item,user

app = FastAPI()

app.include_router(item.router)
app.include_router(user.router)
```
- FastAPI()로 앱 인스턴스를 생성한 뒤, include_router()를 통해 모듈별로 분리된 라우터를 앱에 연결한다.
- routes/item.py, routes/user.py등 라우터 파일에서 APIRouter로 정의된 라우팅들을 **FastAPI 앱에 통합하는 작업**이다.