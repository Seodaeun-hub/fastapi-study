from fastapi import FastAPI
from enum import Enum

app = FastAPI()

# http://localhost:8081/items/3
# decorator에 path값으로 들어오는 문자열중에 
# format string { }로 지정된 변수가 path parameter
@app.get("/items/{item_id}")


# 수행 함수 인자로 path parameter가 입력됨. 
# 함수 인자의 타입을 지정하여 path parameter 타입 지정.
async def read_item(item_id: int): #pydantic에서 오류를 나타내준다.
    return {"item_id": item_id} #content-type : application/json

# Path parameter값과 특정 지정 Path가 충돌되지 않도록 endpoint 작성 코드 위치에 주의 
@app.get("/items/all")
# 수행 함수 인자로 path parameter가 입력됨. 함수 인자의 타입을 지정하여 path parameter 타입 지정.  
async def read_all_items():
    return {"message": "all items"}

#순차적으로 path를 찾기 때문에 위에꺼가 매핑이 되므로 items/all로 된다면 오류가 발생한다.
#고정된 값을 사용할 때는 반드시 맨 위로 올려야한다.
