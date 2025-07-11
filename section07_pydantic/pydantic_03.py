from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class User(BaseModel):
    username: str = Field(..., description="The user's username", example="john_doe")
    email: str = Field(..., description="The user's email address", example="john.doe@example.com")
    password: str = Field(..., min_length=8, description="The user's password")
    age: Optional[int] = Field(None, ge=0, le=120, description="The user's age, must be between 0 and 120", example=30)
    is_active: bool = Field(default=True, description="Is the user currently active?", example=True)
#password는 최소 8글자
#age는 0세 이상이고 120 이하여야한다.
#is_active defalut는 기본값. 숫자값(0,1)로 넣으면 False,True로 나옴.
# Example usage

try:
    user = User(username="john_doe", email="john.doe@example.com", password="Secret123")
    print(user)
except ValidationError as e:
    print(e.json())

'''
https://docs.pydantic.dev/2.8/concepts/fields/

gt - greater than >
lt - less than <
ge - greater than or equal to >=
le - less than or equal to <=
multiple_of - a multiple of the given number 배수
allow_inf_nan - allow 'inf', '-inf', 'nan' values 
'''

class Foo(BaseModel):
    positive: int = Field(gt=0)
    non_negative: int = Field(ge=0)
    negative: int = Field(lt=0)
    non_positive: int = Field(le=0)
    even: int = Field(multiple_of=2) #2의 배수
    love_for_pydantic: float = Field(allow_inf_nan=True)
    #allow_inf_nan=False (무한대 허용 안됨.)


foo = Foo(
    positive=1,
    non_negative=0,
    negative=-1,
    non_positive=0,
    even=2,
    love_for_pydantic=float('inf'),
)
print(foo)

'''
https://docs.pydantic.dev/2.8/concepts/fields/

min_length: 문자열 최소 길이
max_length: 문자열 최대 길이
pattern: 문자열 정규 표현식 (많이 사용함.)
'''

class Foo(BaseModel):
    short: str = Field(min_length=3)
    long: str = Field(max_length=10)
    regex: str = Field(pattern=r'^\d*$')  #숫자값으로 이뤄져야한다.


foo = Foo(short='foo', long='foobarbaz', regex='123')
print(foo)
#> short='foo' long='foobarbaz' regex='123'
'''
max_digits: Decimal 최대 숫자수. 소수점 앞에 0만 있는 경우나, 소수점값의 맨 마지막 0는 포함하지 않음. 
decimal_places: 소수점 자리수 . 소수점값의 맨 마지막 0는 포함하지 않음
'''

from decimal import Decimal

class Foo(BaseModel):
    precise: Decimal = Field(max_digits=5, decimal_places=2)
#103.25, 103.25000 가능. 
#0.25, 0000000.25도 가능. (소수점 앞에 0과 맨뒤 0은 포함하지 않음)

foo = Foo(precise=Decimal('123.45'))
print(foo)
#> precise=Decimal('123.45')