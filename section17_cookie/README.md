# Section 17 - Cookie 기반 사용자 인증 및 Signed Cookie 이해
# 1. 왜 Cookie를 사용하는가?
- **Web은 Stateless하다.**
- HTTP 요청은 상태를 유지하지 않는(stateless) 프로토콜이다.
- 사용자가 로그인했다고 해도 다음 요청에서 서버는 "누가 로그인했는지" 알 수 없다. 
- **상태 유지를 위한 방법 : Cookie**
- 서버가 사용자의 브라우저에 정보를 저장하고, 브라우저는 이후 요청 시 Cookie를 자동으로 포함시킴.
- 서버는 이 Cookie를 바탕으로 사용자의 상태(예:로그인 여부)를 파악할 수 있다.

# 2. Cookie의 구조와 작동 원리
- Cookie는 key-value 쌍으로 저장됨.
```python
my_cookie = "gildong@gmail.com"  # key: my_cookie, value: 이메일
```
- 브라우저는 요청 시 마다 이 Cookie를 포함하여 서버로 전송함.
- 서버는 요청의 Request.cookies에서 이를 확인할 수 있음. 

# main_cookie.py - FastAPI에서 Cookie 기반 인증 처리
- 이 코드는 FastAPI로 만든 간단한 웹 앱에서 사용자의 로그인 상태를 Cookie를 통해 유지하는 구조이다.
- 사용자가 로그인에 성공하면 서버는 my_cookie라는 이름의 쿠키를 생성해 클라이언트에 전달하고, 사용자의 다음 요청에서는 이 쿠키를 확인해 로그인 상태를 식별한다.
- **쿠키 기반 인증의 핵심은 다음과 같다:**
- 로그인 성공 시: 쿠키에 사용자 정보를 저장하고 클라이언트에 전달
- 요청 시마다: 서버는 쿠키를 읽고 로그인 여부를 판단
- 로그아웃 시: 쿠키 삭제로 상태 초기화

## 1. 사용자 데이터 베이스
```python
users_db = {
    "gildong@gmail.com": {
        "username":"gildong",
        "email":"gildong@gmail.com",
        "password":"fastapi"
    }
}
```
- 실습용 사용자 정보가 딕셔너리 형태로 구성되어 있음.
- 실제로는 DB에서 불러오겠지만, 여기선 예제 목적의 하드코딩된 사용자 정보.

## 2. 쿠키에서 사용자 정보 추출 함수 (방법 1)
```python
def get_logged_user(request: Request):
    cookies = request.cookies
    if "my_cookie" in cookies.keys():
        my_cookie_value = cookies["my_cookie"]
        cookie_user = json.loads(my_cookie_value)
        return cookie_user
    return None
```
- Request.cookies : 모든 쿠키가 딕셔너리로 제공됨.
- my_cookie라는 key를 기준으로 사용자 정보를 가져옴.
- 쿠키에는 JSON 문자열이 들어있으므로 json.loads()로 다시 dict로 변환.
- 반환된 cookie_user는 {"username": ..., "email": ...} 형태의 사용자 정보이다.
- **주의 : 쿠키는 문자열이기 때문에 객체형으로 사용하려면 항상 json.loads() 처리가 필요하다**

## 3. 쿠키 추출 (방법 2 - FastAPI 의존성 활용)
```python
def get_logged_user_by_cookie_di(my_cookie=Cookie(None)):
    if not my_cookie:
        return None
    cookie_user = json.loads(my_cookie)
    return cookie_user
```
- Cookie()는 FastAPI가 제공하는 의존성 주입 도구.
- **my_cookie=Cookie(None)**구문을 통해 FastAPI는 요청 쿠키에서 "my_cookie"값을 자동으로 추출
- 더 깔끔하고 선언적인 방식이라 실무에서도 선호됨.
- 이 방식은 FastAPI의 Depends()와 함께 사용할 수 있어 라우터 함수에서 매우 유용하게 사용.

## 4. 홈 화면
```python
@app.get("/")
async def read_root(cookie_user: dict = Depends(get_logged_user_by_cookie_di)):
    if not cookie_user:
        return HTMLResponse("로그인 하지 않았습니다...", status_code=401)
    return HTMLResponse(f"환영합니다. {cookie_user['username']}님")
```
- 이 페이지는 사용자가 로그인했는지 쿠키를 기준으로 확인
- **Depends()를 통해 쿠키 정보 자동 주입.**
- 로그인하지 않았으면 로그인 링크와 함께 401 응답 보냄.
- 로그인한 경우 사용자명을 포함한 환영 메시지 출력.

## 5. 로그인 폼
```python
@app.get("/login")
async def login_form():
    return HTMLResponse("""
    <form action="/login" method="post">
        Email: <input type="email" name="email"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    """)
```
- 단순 HTML 폼을 반환하는 라우트
- 사용자의 이메일과 비밀번호를 입력받아 POST 요청을 보냄.

## 6. 로그인 처리
```python
@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    user_data = users_db[email]
    
    if not user_data or user_data["password"] != password:
        raise HTTPException(status_code=401, detail="Email과 Password가 일치하지 않습니다")
```
- 로그인 입력값을 Form(...)으로 추출.
- 이메일이 존재하고 비밀번호가 맞는지 확인 후 실패시 401 에러 발생.

```python
    user_json = json.dumps({"username": user_data["username"], "email": user_data["email"]})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="my_cookie", value=user_json, httponly=True, max_age=3600)
```
- 로그인 성공 시 사용자 정보를 JSON 문자열로 쿠키에 저장.
- **set_cookie() 함수 설명** :
- key : 쿠키 이름
- value : 쿠키 값
- httponly : JS로 접근 금지 (보안 강화)
- max_age : 유효시간 (초) -> 이걸 생략하면 세션 쿠키로 동작함.

## 7. 사용자 프로필 조회
```python
@app.get("/user_profile")
async def user_profile(cookie_user: dict = Depends(get_logged_user_by_cookie_di)):
    if not cookie_user:
        return HTMLResponse("로그인 하지 않았습니다...", status_code=401)
    return HTMLResponse(f"{cookie_user['username']}님의 email 주소는 {cookie_user['email']}")
```
- /user_profile 접근 시 쿠키를 확인해 로그인 여부 판단.
- 쿠키 기반으로 로그인된 사용자 정보를 화면에 표시.

## 8. 로그아웃
```python
@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("my_cookie")
    return response
```
- 로그아웃 처리 시 쿠키를 명시적으로 삭제
- RedirectResponse 객체를 반환하면서 홈으로 이동.

# 헷갈리는 부분 정리
## 1. 왜 JSON 문자열을 쿠키에 저장할까?
- 쿠키는 문자열(string)만 저장 가능하다.
- HTTP 쿠키는 기본적으로 문자열만 저장할 수 있다. 그러므로 dict, list 같은 python 객체는 직접 쿠키에 넣을 수 없다.
```python
# 이런 건 안 됨
response.set_cookie(key="my_cookie", value={"username": "gildong", "email": "gildong@gmail.com"})
```
-> 그러므로 딕셔너리를 문자열로 변환해야 하는데, 그때 쓰는 것이 JSON이다.

## 2. dict -> JSON -> dict 변환 흐름
1. dict를 **JSON 문자열로 변환** : **json.dumps()** 사용 
예시) {"username": "gildong"} → '{"username": "gildong"}'
2. 쿠키에 저장 : 문자열만 가능하므로 문제 없음
예시) set_cookie(..., value=user_json)
3. 다시 꺼낼 때 **dict로 복원** : **json.loads()** 사용
예시) '{"username": "gildong"}' → {"username": "gildong"}

```python
user = json.loads(my_cookie)  # 문자열을 dict로 복원
print(user["username"])       # → gildong
```
```python
# 잘못된 방식
print(my_cookie["username"])  # ❌ 문자열은 key로 접근 불가
```

# main_sessmiddle.py - SessionMiddleware를 이용한 세션 로그인 구현
- SessionMiddleware는 FastAPI에 기본 제공되는 미들웨어로, 쿠키에 서명된 세션 정보를 저장하고 관리할 수 있게 해줌.
- 로그인한 사용자 정보를 request.session 딕셔너리에 저장하고, 다음 요청에서 그 정보를 꺼내 인증 상태를 유지함.
- 쿠키에는 실제 데이터가 아닌, 서명된(signed) JSON 데이터가 담기므로 위변조 방지가 가능함.

## 1. SessionMiddleware란?
```python
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=3600)
```
- 클라이언트가 로그인하면 서버는 request.session["key"] = value 식으로 사용자 데이터를 저장함.
- 이후 응답 시, 이 세션 딕셔너리를 JSON으로 직렬화 -> 서명(signed) -> 쿠키로 저장함.
- 다음 요청에서는 클라이언트가 그 쿠키를 다시 보내고, 서버는 서명을 검증한 뒤 request.session에 복원함.
- 이렇게 하면 서버가 상태를 기억하는 것 처럼 보이지만, 실제 데이터는 쿠키에 있음 (stateless + 보안 강화)

## 2. 비밀키 생성 및 설정
```python
import secrets

# Generate a secure random key (e.g., 32 bytes)
secret_key = secrets.token_hex(32)
print(f"Your secret key: {secret_key}")
```
- 위 코드로 생성한 키는 .env 파일에 저장하고 사용
```python
# .env
SECRET_KEY=91adbcf5b3b7c6c793f9e1c02cf83e91e56eeea2d11cfed83e87bc3e007dadbe
```

## 3. 환경 변수 불러오기 & 미들웨어 등록
```python
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=3600)
```
- SessionMiddleware는 secret_key 없이 동작하지 않으며, 반드시 등록해야한다.
- max_age=3600 : 쿠키 유지 시간 1시간 -> 브라우저가 닫혀도 쿠키 유지됨
- 설정하지 않으면 기본은 2주
- None으로 설정하면 브라우저가 꺼질 때 쿠키 삭제됨 (session cookie)

## 4. 사용자 정보
```python
users_db = {
    "gildong@gmail.com": {
        "username": "gildong",
        "email": "gildong@gmail.com",
        "password": "fastapi"
    }
}
```
- 연습용 DB

## 5. 로그인 구현
```python
@app.get("/login")
async def login_form():
    # Simple login form
    return HTMLResponse("""
    <form action="/login" method="post">
        Email: <input type="email" name="email"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    """)

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user_data = users_db.get(email)
    # DB에 있는 email/password가 Form으로 입력 받은 email/password가 다를 경우 HTTPException 발생.
    if not user_data or user_data["password"] != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Email과 Password가 일치하지 않습니다")

    # FastAPI의 Response 객체에 signed cookie 값 설정. 
    session = request.session #dictionary 값.
    session["session_user"] = {"username": user_data["username"], "email": user_data["email"]}
    
    # response 객체에 set_cookie()를 호출하지 않아야 함. 자동으로 cookie값 설정됨. 
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
```
- request.session은 서버에서 관리되는게 아니라, 내부적으로 JSON->문자열->서명->쿠키저장->클라이언트 전송
- 다음 요청에 이 쿠키가 다시 오면 -> 서버는 서명 검증 후 다시 request.session으로 복원.
- **여기서 주의!!**
-**우리는 그냥 딕셔너리를 request.session에 집어넣기만 하면 그 다음 과정(JSON으로 변환->서명->쿠키로 전달)은 모두 FastAPI + SessionMiddleware가 자동으로 처리해줌.**

## 6. 인증 유지 및 사용자 정보 접근
```python
# 인증 여부 확인 함수
def get_session_user(request: Request):
    session = request.session
    if "session_user" not in session:
        return None
    return session["session_user"]
```
- 다음 요청이 오면 FastAPI는 클라이언트가 보낸 signed cookie를 받고 그걸 다시 secret_key로 검증하고 복호화함. 내부적으로 JSON을 다시 딕셔너리로 로딩함. 결과로 request.session["session_user"]가 다시 딕셔너리로 살아남.

```python
# 인증된 사용자만 접근 가능한 페이지
@app.get("/")
async def read_root(request: Request, session_user: dict = Depends(get_session_user)):
    if not session_user:
        return HTMLResponse("로그인 하지 않았습니다...", status_code=401)
    return HTMLResponse(f"환영합니다. {session_user['username']}님")
```
- Depends()로 인증 정보를 불러와 로그인 여부 판단.

## 7. 로그아웃
```python
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
```
- **request.session.clear()**를 통해 세션 데이터를 초기화한다.
- 브라우저는 쿠키는 그대로 갖고 있지만, 서명된 데이터가 없기 때문에 인증이 해제된다.

## 8. 브라우저 동작 (세션 흐름)
1. 로그인 POST 요청
2. 서버가 세션에 사용자 정보 저장 (request.session)
3. FastAPI가 JSON 직렬화 → 서명 → 쿠키 생성 → 클라이언트에 전달
4. 클라이언트가 다음 요청에 해당 쿠키를 자동 포함
5. FastAPI가 쿠키 복호화 & 서명 검증 → 세션 복원
6. 로그아웃 시 세션 정보 삭제

## 9. 핵심 요약
| 구성 요소                       | 설명                            |
| --------------------------- | ----------------------------- |
| `SessionMiddleware`         | FastAPI에서 쿠키 기반 세션을 구현하는 미들웨어 |
| `secret_key`                | 쿠키 위변조를 막기 위한 서명 키            |
| `request.session`           | 로그인 사용자 정보 저장 및 조회            |
| `.clear()`                  | 세션 로그아웃 처리                    |
| `Depends(get_session_user)` | 인증 정보 불러오기                    |
 

 # main_cookie.py vs main_sessmiddle.py 핵심 차이 요약
 | 항목 | `main_cookie.py` (일반 쿠키 방식) | `main_sessmiddle.py` (SessionMiddleware 방식) |
|------|-----------------------------------|--------------------------------------------|
| **데이터 저장 위치** | 사용자의 정보를 JSON 문자열로 **직접 쿠키에 저장** | `request.session` 딕셔너리에 저장 → **FastAPI가 자동으로 쿠키에 인코딩 & 서명** |
| **데이터 직렬화** | `json.dumps()`로 **우리가 직접 JSON 문자열로 변환** | **자동으로 JSON 문자열로 직렬화됨** |
| **보안** | 민감 정보가 **직접 브라우저에 노출됨** (위험) | `secret_key`로 서명된 **signed cookie**로 정보 변조 방지 |
| **개발자 부담** | `set_cookie()`, `get_cookie()` 직접 다뤄야 함 | 그냥 `request.session["key"]`로 다룰 수 있음 (직관적) |
| **자동 만료 설정** | `set_cookie(..., max_age=...)`로 수동 지정 | `SessionMiddleware(..., max_age=...)`에서 자동 관리 |
| **복잡도** | 구조는 단순하지만 보안, 유지보수 이슈 있음 | 구조는 살짝 복잡하지만 **보안 + 확장성** 우수 |
