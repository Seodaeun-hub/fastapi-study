from fastapi import FastAPI
from typing import Optional

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

# http://localhost:8081/items?skip=0&limit=2
@app.get("/items")
# 함수에 개별 인자값이 들어가 있는 경우 path parameter가 아닌 모든 인자는 query parameter
# query parameter의 타입과 default값을 함수인자로 설정할 수 있음.
async def read_item(skip: int = 0, limit: int = 2):
    return fake_items_db[skip: skip + limit]

#인자값이 무조건 같아야한다.
#만약에 skip_x로 주어진다면 skip이 안들어왔다고 생각하고 skip의 default값인 0으로 들어가서 오류가 발생하지 않음.

@app.get("/items_nd/")
# 함수 인자값에 default 값이 주어지지 않으면 반드시 query parameter에 해당 인자가 주어져야 함.  
async def read_item_nd(skip: int, limit: int):
    return fake_items_db[skip : skip + limit]
#skip이랑 limit 인자가 안들어오면 pydantic에서 오류를 발생시킨다.


@app.get("/items_op/")
# 함수 인자값에 default 값이 주어지지 않으면 None으로 설정. 
# limit: Optional[int] = None 또는 limit: int | None = None 과 같이 Type Hint 부여  
async def read_item_op(skip: int, limit: Optional[int] = None ):
    # return fake_items_db[skip : skip + limit]
    if limit:
        return fake_items_db[skip : skip + limit]
    else:
        return {"limit is not provided"} #limit가 None이 들어올경우
#Optional을 쓸 때는 default값을 반드시 선언해줘야한다. (None, 3 등)

# Path와 Query Parameter를 함께 사용.
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None): #q:Opitional[str]=None과 같음
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}   