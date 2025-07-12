# Section 07 - Pydantic 모델과 데이터 유효성 검사

# 학습 주제
- FastAPI에서 Pydantic 모델을 활용한 요청 데이터 타입 선언과 자동 유효성 검사
- Form 데이터와 JSON 데이터 처리 방식의 차이점과 유효성 검증 적용 방법
- 기본 필드 검증 (Field), 엄격 모드 (Strict), 정규식/숫자/이메일/URL/IP 등 다양한 검증 기법
- @field_validator, @model_validator를 통한 커스텀 유효성 검사 구현
- Depends() + Form 조합을 통해 검증 로직을 함수로 분리하여 재사용성과 테스트 용이성 확보


# 핵심 개념 정리 (pydantic_01)
**1. Pydantic 모델을 사용한 class 선언**
```python
from pydantic import BaseModel, ValidationError
from typing import List, Optional
import json

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None

user = User(id=10, name="test_name", email="tname@example.com", age=40)
print("user:", user, user.id)
```
- Pydantic Model 선언할 때 반드시 BaseModel 상속 받아야함.
- class는 ":" 사용, "=" 아님.
- **주의사항** : User(10, 'test_name', 'tname@example.com', 40) 하지 않도록 유의
- 반드시 argument 명을 쳐줘야함. (선언한 class와 매핑 해줘야 함.)

**2. dict keyword argument(kwargs)로 Pydantic Model 객체화**
```python
user_from_dict = User(**{"id": 10, "name": "test_name", "email": "tname@example.com", "age": 40})
print("user_from_dict:", user_from_dict, user_from_dict.id)
```
- **{"":, "":,...} -> keyword argument로 나옴. (id=10, name="test_name",email="tname@example.com", age=40)

**3. json 문자열 기반 Pydantic Model 객체화**
```python
json_string = '{"id": 10, "name": "test_name", "email": "tname@example.com", "age": 40}'
json_dict = json.loads(json_string)
user_from_json = User(**json_dict)
print("user_from_json:", user_from_json, user_from_json.id)
```
- 위에 꺼랑 같게 나옴.

**4. Pydantic Model의 상속**
```python
class AdvancedUser(User):
    advanced_level: int
adv_user = AdvancedUser(id=10, name="test_name", email="tname@example.com", age=40, advanced_level=9)
print("adv_user:", adv_user)
```
- 위의 User class의 4개의 속성을 가져온 후 하나의 속성 추가

**5. 내포된(Nested된 Json) 데이터 기반 Pydantic Model 생성**
```python
class Address(BaseModel):
    street: str
    city: str

class UserNested(BaseModel):
    name: str
    age: int
    address: Address

json_string_nested = '{"name": "John Doe", "age": 30, "address": {"street": "123 Main St", "city": "Anytown"}}'
json_dict_nested = json.loads(json_string_nested)

user_nested_01 = UserNested(**json_dict_nested)
print("user_nested_01:", user_nested_01, user_nested_01.address, user_nested_01.address.city)

user_nested_02 = UserNested(
    name="test_name", age=40, address = {"street": "123 Main St", "city": "Anytown"}
)
print("user_nested_02:", user_nested_02, user_nested_02.address, user_nested_02.address.city)
```
- UserNested 클래스에 Address 클래스를 인자로 받을 수 있음.

**6. python 기반/json 문자열 기반으로 pydantic serialization**
```python
#python 기반
user_dump_01 = user.model_dump()
print(user_dump_01, type(user_dump_01))
#json 기반
user_dump_02 = user.model_dump_json()
print(user_dump_02, type(user_dump_02))
```
- user.model_dump()는 user 객체를 Python의 기본 자료형(dict)로 변환.
예) {'id': 1, 'name': 'Alice'} <class 'dict'>
-> 다른 Python 코드에서 JSON으로 변환하기 전에 사용하거나, dict로 처리할 때 사용.
- user.model_dump_json()는 user 객체를 JSON 문자열(str)로 직렬화한다.
예) {"id":1,"name":"Alice"} <class 'str'>
-> API 응답으로 JSON을 보낼 때, 저장할 때, 네트워크로 전송할 때 사용.

# 핵심 개념 정리 (pydantic_02)
**1. Stirct() 모드 설정**
```python
from pydantic import BaseModel, ValidationError, ConfigDict, Field, Strict
from typing import List, Annotated #typehint

class Address(BaseModel):
    street: str
    city: str
    country: str
class User(BaseModel):
    id: int
    name: str
    email: str
    addresses: List[Address]
    age: Annotated[int, Strict()] = None
    # age: int = Field(None, strict=True)
```
- **문자열->숫자값 자동 파싱을 허용하지 않을 경우 Strict 모드로 설정.**
(안 할 경우, 자동으로 파싱해줌.)
- age: Annotated[int, Strict()] = None
개별 속성에 Strict 모드 설정 시 Fiedl나 Annotated 이용. 
None 적용 시 Optional
- 전체 모델에 Strict() 모드 적용 시
첫째줄에 적기. **model_config = ConfigDict(strict=True)**

**2. Pydantic Model 객체화 시 자동 검증, 검증 오류시 ValidationError raise**
```python
try:
    user = User(
        id=123,
        name="John Doe",
        email="john.doe@example.com",
        addresses=[{"street": "123 Main St", "city": "Hometown", "country": "USA"}],
        age="29" # 문자열 값을 자동으로 int 로 파싱함.
    )
    print(user)
except ValidationError as e:
    print("validation error happened")
    print(e)
```
- 위에서 언급했듯이, Strict 모드를 쓰지 않을 경우 "29:->29로 자동으로 파싱해줌.
- class에 정의한 조건에 맞지 않을 경우, ValidationError 발생.

# 핵심 개념 정리 (pydantic_03)
**1. 검증 오류**
```python
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class User(BaseModel):
    username: str = Field(..., description="The user's username", example="john_doe")
    email: str = Field(..., description="The user's email address", example="john.doe@example.com")
    password: str = Field(..., min_length=8, description="The user's password")
    age: Optional[int] = Field(None, ge=0, le=120, description="The user's age, must be between 0 and 120", example=30)
    is_active: bool = Field(default=True, description="Is the user currently active?", example=True)

try:
    user = User(username="john_doe", email="john.doe@example.com", password="Secret123")
    print(user)
except ValidationError as e:
    print(e.json())
```
- Field()안에 생성.
- password는 최소 8글자
- age는 0세 이상, 120 이하
- is_active의 default 값은 True. 숫자값(1 or 0) 넣으면 True, False로 반환.

**2. 숫자형 검증 오류**
- gt - greater than >
- lt - less than <
- ge - greater than or equal to >=
- le - less than or equal to <=
- multiple_of - a multiple of the given number 배수
- allow_inf_nan - allow 'inf', '-inf', 'nan' values 

예)
```python
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
```
- allwo_ing_nan=True -> 무한대 허용.

**3. 문자열 검증 오류**
- min_length: 문자열 최소 길이
- max_length: 문자열 최대 길이
- pattern: 문자열 정규 표현식 (많이 사용함.)

예) 
```python
class Foo(BaseModel):
    short: str = Field(min_length=3)
    long: str = Field(max_length=10)
    regex: str = Field(pattern=r'^\d*$')

foo = Foo(short='foo', long='foobarbaz', regex='123')
print(foo)
```
**pattern**
- 영문자만 : ^[A-Za-z]+$
- 숫자만 : ^[0-9]+$
- 영어+숫자 : ^[A-Za-z0-9]+$
- 아이디(3~20자, 영숫자+언더바) : ^[a-zA-Z0-9_]{3,20}$
- 비밀번호(영문+숫자+특수문자,8~20자): ^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,20}$
- 이메일 : ^[\w\.-]+@[\w\.-]+\.\w{2,4}$
- 핸드폰 번호(숫자만) : ^01[016789][0-9]{7,8}$
- 날짜 (YYYY-MM-DD) : ^\d{4}-\d{2}-\d{2}$
- 주민등록번호 앞자리 : ^\d{6}$

**4. Decimal**
- max_digits: Decimal 최대 숫자수. 소수점 앞에 0만 있는 경우나, 소수점값의 맨 마지막 0는 포함하지 않음. 
- decimal_places: 소수점 자리수 . 소수점값의 맨 마지막 0는 포함하지 않음
예) 103.25, 103.25000000 가능
예) 0.25, 00000000.25 가능 
(소수점 앞에 0과 맨 뒤 0은 포함하지 않음)

예)
```python
from decimal import Decimal
class Foo(BaseModel):
    precise: Decimal = Field(max_digits=5, decimal_places=2)
foo = Foo(precise=Decimal('123.45'))
print(foo)
```

# 핵심 개념 정리 (pydantic_04)
**1. email 검증**
```python
from pydantic import BaseModel, EmailStr, Field

class UserEmail(BaseModel):
    email: EmailStr
try:
    user_email = UserEmail(email="user@examples.com")
    print(user_email)
except ValueError as e:
    print(e)
```
- email 검증할 때는 pydantic의 EmailStr 사용
- email: EmailStr = Field(..., max_length=40) #Field와 함께 사용.

**2. url 검증**
1)  HttpUrl: http 또는 https만 허용. TLD(top-level domain)와 host명 필요. 최대 크기 2083
- valid: https://www.example.com, http://www.example.com, http://example.com
- invalid: ftp://example.com

2) AnyUrl: http, https, ftp 등 어떤 프로토콜도 다 허용. host 명 필요하며 TLD 필요 없음. 
- valid: http://www.example.com ftp://example.com, ksp://example.com ftp://example
- invalid: ftp//example.com (://만 지키기)

3) AnyHttpUrl: http 또는 https만 허용, TLD는 필요하지 않고 host명은 필요.
- valid: https://www.example.com, http://www.example.com, http://example.com
- invalid: ftp://example.com (거의 HttpUrl과 비슷.)

4) FileUrl: 파일 프로토콜만 허용. host 명이 필요하지 않음. 
- valid: file:///path/to/file.txt

예)
```python
from pydantic import HttpUrl, AnyUrl, AnyHttpUrl, FileUrl

class UserResource(BaseModel):
    http_url: HttpUrl
    any_url: AnyUrl
    any_http_url: AnyHttpUrl
    file_url: FileUrl
    
try:
    user_resource = UserResource(
        http_url="https://www.example.com",
        any_url="ftp://example.com",
        any_http_url="http://www.example.com",
        file_url="file:///path/to/file.txt"
    )

    print(user_resource, user_resource.http_url)
except ValueError as e:
    print(f"Validation error: {e}")
```
- url을 검증할 때는 pydantic의 HttpURL, AnyUrl, AnyHttpUrl, FileUrl 사용

**3. ip 검증**
1) IPvAnyAddress : IPv4Address or an IPv6Address
- valid: 192.168.1.1, 192.168.56.101
- invalid: 999.999.999.999 (255에 들어가야됨.)
2) IPvAnyNetwork : IPv4Network or an IPv6Network
- valid: 192.168.1.0/24
- invalid: 192.168.1.0/33
3) IpvAnyInterface : IPv4Interface or an IPv6Interface
- valid: 192.168.1.1/24
- invalid: 192.168.1.1/33

예)
```python
from pydantic import IPvAnyAddress, IPvAnyNetwork, IPvAnyInterface

class Device(BaseModel):
    ip_address: IPvAnyAddress
    network: IPvAnyNetwork
    interface: IPvAnyInterface

try:
    device = Device(
        ip_address="192.168.1.1",
        network="192.168.1.0/24",
        interface="192.168.1.0/24")
    print(device)
except ValueError as e:
    print(e)
```
- IP를 검증할 때는 pydantic의 IPvAnyAddress, IPvAnyNetwork, IPvAnyInterface 사용

**4. pydantic-extra-types 검증**
```python
from pydantic_extra_types.country import CountryAlpha3

class Product(BaseModel):
    made_in: CountryAlpha3

product = Product(made_in="USA")
print(product)
```
- pip install pydantic-extra-types pycountry 설치 필요
- https://docs.pydantic.dev/latest/api/pydantic_extra_types_color/

# 핵심 개념 정리 (pydantic_05)
*vaildation custom하는 방법*
**1. field_vaildator : 개별 필드 값 검증**
```python
from pydantic import BaseModel,  ValidationError, field_validator, model_validator
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    confirm_password: str
    
    @field_validator('username')

    def username_must_not_be_empty(cls, value: str):
        if not value.strip():
            raise ValueError("username must not be empty")
        return value
```
- cls는 클래스 메서드로 쓰기 위한 필수 인자
- value는 해당 필드에 입력된 값.
- strip()을 써서 공백만 있는 값도 막음
- 유효하지 않으면 valueErrror 발생

**2. field_validator : 비밀번호 조건 검증**
```python
    @field_validator('password')
    def password_must_be_strong(cls, value: str):
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in value):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in value):
            raise ValueError('Password must contain at least one letter')
        return value
```
- 길이, 숫자 포함, 알파벳 포함 여부 확인
- any()로 한 글자라도 조건 만족하면 통과
예) sec012345 (isdigit(숫자냐))
    00011111 -> 하나라도 1이 있으면 1, 다 0이면 0 

**3. model_validator : 여러 필드 관계 검증**
**여러 필드가 동시에 유효해야 할 때는 model_validator 사용**
```python
    @model_validator(mode='after')
    def check_passwords_match(cls, values):
        password = values.password
        confirm_password = values.confirm_password
        if password != confirm_password:
            raise ValueError("Password do not match")
        return values

try:
    user = User(username="john_doe", password="Secret123", confirm_password="Secret123")
    print(user)
except ValidationError as e:
    print(e)
```
- mode='after' : 필드 검증이 **끝난 후**에 실행
- values : 전체 모델 인스턴스를 의미
- 비밀번호와 확인값이 일치하는지 검사
- 테스트 : 예외 발생 시 pydantic의 ValidationError가 자동 포맷으로 에러 메시지 출력.

# 핵심 개념 정리 (main.py), (schemas/item_schema.py)
**Pydantic Custom Validation + Form 처리**
**왜 Form 필드 검증과 Pydantic 모델 검증을 나눠서 하는가?**
- 단순한 개별 조건은 Form 필드에서 바로 검증한다.
- 필드 간 관게 조건이 필요한 경우에는 Pydantic 모델을 사용해야한다.

**1. python 모델 선언**
```python
# schemas/item_schema.py
from pydantic import BaseModel, Field, model_validator

class Item(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(None, max_length=500)
    price: float = Field(..., ge=0)
    tax: float = None

    #필드 간 유효성 검사 (예 : tax<price )
    @model_validator(mode='after')
    def tax_must_be_less_than_price(cls, values):
        if values.tax is not None and values.tax > values.price:
            raise ValueError("Tax must be less than price")
        return values
```
```python
# Form 데이터를 받아 Item 모델로 변환
def parse_user_form(
    name: str = Form(..., min_length=2, max_length=50),
    description: Annotated[str, Form(max_length=500)] = None,
    price: float = Form(..., ge=0),
    tax: Annotated[float, Form()] = None, 
) -> Item:
    try: 
        item = Item(
            name = name,
            description = description,
            price = price, 
            tax = tax
        )

        return item
    except ValidationError as e:
        raise RequestValidationError(e.errors()) 
```


2. **라우터 예제 및 설명**
**2-1) Query + Body (기본 모델 검증)**
```python
@app.put("/items/{item_id}")
async def update_item(item_id: int, q: str, item: Item=None):
    return {"item_id": item_id, "q": q, "item": item}
```
- Item은 JSON Body로 들어옴
- model_validator 등 모든 검증 자동 적용.

**2-2) Path + Query + Body (JSON 기반 검증)**
```python
@app.put("/items_json/{item_id}") 
async def updata_item_json(
    item_id:int = Path(..., gt=0),
    q1: str = Query(None, max_length=50),
    #q1: Annotated[str, Query(max_length=50)] = None
    q2: str = Query(None, min_length=3),
    #q2: Annotated[str, Query(min_length=3)] = None
    item: Item = None
):
    return {"item_id":item_id, "q1":q1,"q2":q2,"item":item}
```
- 쿼리 별 따로 조건 달기.

**2-3) Form : Form 필드별 직접 검증 (cross-field 불가)**
```python
@app.post("/items_form/{item_id}")
async def update_item_form(
    item_id: int = Path(..., gt=0, title="The ID of the item to get"),
    q: str = Query(None, max_length=50),
    name: str = Form(..., min_length=2, max_length=50),
    description: Annotated[str, Form(max_length=500)] = None,
    #description: str = Form(None, max_length=500),
    price: float = Form(..., ge=0), 
    tax: Annotated[float, Form()] = None
    #tax: float = Form(None)
):
    return {"item_id": item_id, "q": q, "name": name, 
            "description": description, "price": price, "tax": tax}
```
- Form 필드에서 min_length, ge, max_length는 검증 가능하지만 필드 간 비교 (예: tax < price) 는 불가능

**2-4) Form -> Item 직접 생성 : 모델 검증 수동 적용**
```python
@app.post("/items_form_01/{item_id}")
async def update_item_form_01(
    item_id: int = Path(..., gt=0, title="The ID of the item to get"),
    q: str = Query(None, max_length=50),
    name: str = Form(..., min_length=2, max_length=50),
    description: Annotated[str, Form(max_length=500)] = None,
    #description: str = Form(None, max_length=500),
    price: float = Form(..., ge=0), 
    tax: Annotated[float, Form()] = None
    #tax: float = Form(None)
):
    try:
        item = Item(name=name, description=description, price=price, tax=tax)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    return item
```
- Form + Pydantic 모델 방식으로 Item() 내부에서 검증을 발생시킨다.
- 그러면서 인자를 받고 안에서 검증을 시키게된다. 생성이 될 때 검증을 하면서 @model_validator(mode='after')로 cross-field 유효성 검증이 가능하다.

**2-5) Form + Depends(parse_user_form) : Form 전체를 함수에서 받아 Item 생성 후 검증**
```python
@app.post("/items_form_02/{item_id}")
async def update_item_form_02(
    item_id: int = Path(..., gt=0, title="The ID of the item to get"),
    q: str = Query(None, max_length=50),
    item: Item = Depends(parse_user_form)
):
    return {"item_id": item_id, "q": q, "item": item}
```
- Depends(parse_user_form)을 사용하면 모듈화된 검증 로직을 활용할 수 있어 유지보수에 강하다.
- Depends()는 fastapi에게 불러서 명확하게 넣어줘야한다라는 것을 알리기 위해 사용된다. 함수 같은것이 들어간다.

**왜 Depends()가 유지보수에 강할까?**
1. 로직 분리 (Separation of Concers)
item: Item = Depends(parse_user_form)
- 입력 파싱 & 검증 로직을 라우터 함수에서 분리를 시킨다.
즉 라우터 함수는 비즈니스 로직에만 집중 가능하다.
2. 테스트 용이성 (단위 테스트 가능)
- parse_user_form()은 함수이기 때문에 단독으로 테스트가 가능하다.
- FastAPI 라우터를 호출하지 않고도 Form 검증 로직을 검증할 수 있다.
3. 다른 라우터에서도 재사용이 가능하다.
- 여러 API에서 동일한 Form 구조를 사용할 때 중복 없이 재사용이 가능하다.