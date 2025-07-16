from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from pydantic.dataclasses import dataclass
#데이터를 가져올 때는 검증을 하지않고 넣을 때만 검증하는 경우가 많다. 이미 데베 안에 검증 로직이 들어가있다.
#그러므로 아래 로직을 쓰지 않아도 된다.
class BlogInput(BaseModel) :
    title: str = Field(..., min_length=2, max_length=200)
    author: str = Field(..., max_length=100)
    content: str = Field(..., min_length=2, max_length=4000)
    image_loc: Optional[str] = Field(None,max_length=400) #오류 나올 것임.

class Blog(BlogInput) :
    id : int
    modified_dt: datetime #현재시간으로 됨.

# # 이렇게 검증조건 쓰지말고 사용하기
# class BlogData(BaseModel):
#     id:int
#     title: str
#     author : str
#     content : str
#     modified_dt : datetime
#     image_loc : str|None = None

@dataclass
class BlogData:
    id:int
    title: str
    author : str
    content : str
    modified_dt : datetime
    image_loc : str|None = None #None값이 맨 마지막에 와야함. 중간에 오면 안됨.


