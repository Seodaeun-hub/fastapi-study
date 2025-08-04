# Section 16 - FastAPI 사용자 인증 기능 구현 (bcrypt 기반 비밀번호 해싱/검증)

# 학습 주제
- 사용자의 비밀번호를 안전하게 저장하고 검증하는 로직 구현
- bcrypt 알고리즘을 활용한 해싱 및 인증
- 인증 예외 처리와 UI 연동

"꼼꼼하게 정리해볼까?"

# 1. bycrpt란 무엇인가?
- **bycrpt**는 비밀번호를 안전하게 저장하는 데 사용되는 해시 함수이다. 암호화(복호화 가능)가 아니라 해싱(복호화 불가)방식이며, 입력값 + salt + cost factor를 조합해 매번 다른 해시를 만들어 낸다. bcrypt는 복호화가 불가능한 '단방향 해싱' 알고리즘이며, 사용자가 로그인할 때 입력한 평문 비밀번호를 같은 방식으로 다시 해시하여 DB에 저장된 해시값과 비교한다.
- 핵심 요소
- **salt** : 입력값에 추가되는 임의의 문자열(매번 달라짐)
- **cost factor** : 해싱 반복 횟수 (높을수록 안전하지만 느림)
- **결과 해시** : salt, cost, hash를 모두 포함한 문자열 (DB 저장용)

# 2. auth.py - 사용자 인증 관련 라우터 모듈
- 이 파일은 FastAPI 기반 웹 앱에서 사용자 등록 및 로그인 기능을 담당한다. 내부에는 사용자 입력값 검증, 비밀번호 해싱, 인증 오류 처리 등의 로직이 담겨있다.

## 1. 라우터 생성 및 템플릿 설정
```python
router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")
```
- **prefix="/auth"** : 이 모듈의 모든 라우터는 /auth/로 시작됨.
- **tags=["auth"]** : Swagger 문서에서 보기 편하게 함.
- **templates** : HTML 렌더링에 사용될 템플릿 디렉토리 지정

## 2. 비밀번호 해싱 유틸 함수
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)
```
- **CryptContext** : 다양한 해싱 알고리즘을 지원하나 여기선 bcrypt만 사용.
- **get_hashed_password 함수** : 평문 비밀번호를 안전하게 해시하여 DB에 저장할 때 사용
- **veriry_password 함수** : 로그인 시 사용자가 입력한 비밀번호와 DB에 저장된 해시값을 비교.
- **이때 verify할 대는 .verify 사용하면 간단하게 비교 가능.**

## 3. 사용자 등록 화면 라우트
```python
@router.get("/register")
async def register_user_ui(request : Request):
    return templates.TemplateResponse(
        request=request,
        name="register_user.html",
        context={}
    )
```
- /auth/register GET 요청 시 회원가입 화면을 렌더링해줌.
- Jinja2 템플릿을 사용하여 HTML 페이지로 응답.

## 4. 사용자 등록 처리 라우트
```python
@router.post("/register")
async def register_user(name: str=Form(min_length=2, max_length=100),
                        email: EmailStr = Form(),
                        password: str=Form(min_length=2, max_length=30),
                        conn: Connection = Depends(context_get_conn)):
```
- Form(...)을 사용하여 HTML 폼 데이터를 추출
- FastAPI는 해당 데이터가 없으면 422 오류를 자동으로 발생시킴.
- EmailStr은 이메일 형식 검증 자동화.
- DB 커넥션을 Depends를 통해 의존성 주입 받음.

```python
user = await auth_svc.get_user_by_email(conn=conn, email=email)
    if user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="해당 Email은 이미 등록되어 있습니다.")

    hashed_password = get_hashed_password(password)
    await auth_svc.register_user(conn=conn, name=name, email=email,
                            hashed_password=hashed_password)
    
    return RedirectResponse("/blogs",status_code=status.HTTP_302_FOUND)
    # auth_svc.register_user_...(conn=conn, name=name, email=email, password=password)
```
- 이미 등록된 사용자인 경우 (user로 확인)
- 비밀번호를 안전하게 해싱 후 DB에 저장.
- 가입 후 블로그 홈으로 이동시킴.

## 5. 로그인 화면 라우트
```python
@router.get("/login")
async def login_ui(request : Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )
```
- /auth/login GET 요청 -> 로그인 ui 렌드링

## 6. 로그인 처리 라우트
```python
@router.post("/login")
async def login(email:EmailStr = Form(...),
                password:str = Form(min_length=2, max_length=30),
                conn: Connection = Depends(context_get_conn)):
```
- 사용자로부터 email, password를 Form 방식으로 받음.

```python
    userpass = await auth_svc.get_userpass_by_email(conn=conn, email=email)
    if userpass is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="해당 이메일 사용자는 존재하지 않습니다.")
```
- userpass 객체 안에 들어있는 hashed_password를 가져오는 것. 
- DB에서 사용자의 해시된 비밀번호 조회.

```python
is_correct_pw = verify_password(plain_password=password,
                                     hashed_password=userpass.hashed_password)
    if not is_correct_pw:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="등록하신 이메일과 패스워드 정보가 입력 정보와 다릅니다.")
```
- 해싱된 비밀번호 비교 (verify_password 함수 사용)

```python
    return RedirectResponse("/blogs",status_code=status.HTTP_302_FOUND)
```
- 여기까지 넘어오면 로그인 성공하고 홈으로 이동.

# 3. auth_svc.py - 사용자 인증 서비스 모듈
- 이 파일은 사용자 인증과 관련된 데이터베이스 접근 로직을 처리하는 Service Layer에 해당.
- FastAPI + SQLAlchemy를 사용하는 구조에서, Controller(auth.py) -> Service(auth_svc.py) 흐름으로 분리한 구조이다.

## 주요 역할
1. **사용자 존재 여부 확인** : get_user_by_email()
2. **사용자 + 해시된 비밀번호 조**회 : get_userpass_by_email() 
3. **사용자 등록** : register_user()

## auth_schema.py
```python
from pydantic import BaseModel

class UserData(BaseModel):
    id: int
    name: str
    email: str

class UserDataPASS(UserData):
    hashed_password : str
```
- `UserData`는 로그인이나 회원 조회 시 기본 사용자 정보를 담는 모델.
- `UserDataPASS`는 `UserData`를 상속하며 해시된 비밀번호가 추가된 모델로, 로그인 검증 시 내부적으로만 사용.
- 두 모델을 분리함으로써 API 응답 시 사용자의 민감 정보인 해시 비밀번호가 노출되지 않도록 설계.


## 1. get_user_by_email(conn: Connection, email: str)
```python
async def get_user_by_email(conn: Connection, email: str) -> UserData:
```
- 회원가입 시 중복 이메일인지 확인하기 위해 사용.
- 이메일이 이미 DB에 등록돼 있으면 UserData 객체를 반환하고, 없으면 None을 반환.

```python
try:
            query = f"""
            SELECT id, name, email from user
            where email = :email
            """
            stmt = text(query)
            bind_stmt = stmt.bindparams(email=email)
            result = await conn.execute(bind_stmt)
            # 만약에 한건도 찾지 못하면 None을 던진다. 
            if result.rowcount == 0:
                 return None
                
            row = result.fetchone()
            user = UserData(id=row[0], name=row[1], email=row[2])
            result.close()
            return user
```
- 바인딩된 파라미터 :email로 안전한 쿼리 수행
- 한 명의 사용자만 조회하기 위해 fetchone() 사용
- UserData에 user로 반환

## 2. get_userpass_by_email(conn: Connection, email: str)
```python
async def get_userpass_by_email(conn: Connection, email: str) -> UserDataPASS:
```
- 로그인 시, 사용자가 입력한 비밀번호와 DB에 저장된 해시된 비밀번호를 비교하기 위해 필요한 정보 조회
```python
query = f"""
            SELECT id, name, email, hashed_password from user
            where email = :email
            """
            stmt = text(query)
            bind_stmt = stmt.bindparams(email=email)
            result = await conn.execute(bind_stmt)
            # 만약에 한건도 찾지 못하면 None을 던진다. 
            if result.rowcount == 0:
                 return None
                
            row = result.fetchone()
            userpass = UserDataPASS(id=row[0], name=row[1], email=row[2],
                                hashed_password=row[3])
            result.close()
            return userpass
```
- UserDataPass는 UserData를 상속한 Pydantic 모델로 hashed_password 필드를 추가로 가짐.
- 왜 필요해? FastAPI 컨트롤러(auth.py)에서 verify_password()로 해시 비교 수행하기 위함.

## 3. register_user(conn:Connection, name:str, email:str, hashed_password: str)
```python
async def register_user(conn: Connection, name: str, email: str, hashed_password: str)
```
- 신규 사용자를 DB에 등록하는 기능
- 이때 저장되는 비밀번호는 반드시 해시 처리된 값이어야 함 (auth.py에서 처리)

```python
 try:
        query = f"""
        INSERT INTO user(name, email, hashed_password)
        values ('{name}','{email}','{hashed_password}')
        """
        
        await conn.execute(text(query))
        await conn.commit()
```
- 현재 쿼리는 Python f-string으로 직접 값을 주입함. - 바인딩으로 처리하기.
```python
stmt = text("""
    INSERT INTO user(name, email, hashed_password)
    VALUES (:name, :email, :hashed_password)
""")
await conn.execute(stmt.bindparams(name=name, email=email, hashed_password=hashed_password))
```
- 이렇게 바꾸기
- 데이터베이스 트랜잭션은 여러 작업을 하나의 논리적 단위로 묶어 처리. 사용자 등록은 'insert → commit'이라는 작업 순서로 이루어지므로, 도중에 문제가 생기면 `rollback()`으로 데이터 무결성을 보장.

## main.py
```python
app.include_router(blog.router)
app.include_router(auth.router)
```
- FastAPI에서는 라우터 등록 순서가 중요할 수 있다. /auth 경로에서 인증 관련 쿠키나 인증 미들웨어가 있다면 해당 라우터를 먼저 등록하는 것이 좋음.
- 또한, exception_handler, middleware, CORS, static files 등의 설정이 있다면 router 등록 전에 처리해야함.