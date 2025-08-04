# Section 18 - SessionMiddleware 

# 학습 목표
- FastAPI에서 세션(SessionMiddleware)을 이용한 로그인/로그아웃 기능의 구조와 동작 원리를 이해한다.
- request.session을 통해 사용자 인증 정보를 안전하게 저장하고, 각 요청마다 인증 상태를 유지하는 방식을 습득한다.
- auth_svc.py, auth.py, blog.py 등의 파일을 중심으로 세션 기반 사용자 인증 로직의 구현 흐름을 파악하고 각 모듈의 역할을 구분할 수 있다.
- 선택적/필수적 세션 사용자 정보를 처리하는 get_session_user_opt, get_session_user_prt의 사용 목적을 이해한다.
- 게시물 작성, 수정, 삭제 기능에 세션 기반 권한 검사를 적용하는 실제 애플리케이션 구조를 익힌다.
- 비동기 처리 (async/await) 흐름과 세션 로직이 함께 작동하는 구조를 이해하여, 확장 가능한 인증 기능을 구현할 수 있다.

# auth_svc.py 정리 (SessionMiddleware 기반 인증 처리)
- auth_svc.py는 사용자 인증과 관련된 핵심 서비스 로직을 담고 있는 모듈로, 로그인, 회원가입, 세션정보 조회 등의 기능을 처리함.

## 1. get_user_by_email(conn: Connection, email: str)
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
- 이메일을 기준으로 사용자 존재 여부 확인
- 회원가입 시 중복 확인, 로그인 시 사용자 정보 조회에 사용

## 2. get_userpass_by_email(conn: Connection, email: str)
```python
 try:
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
        userpass = UserDataPASS(id=row[0], name=row[1], email=row[2]
                            , hashed_password=row[3])
        
        result.close()
        return userpass
```
- 로그인 시 비밀번호 비교를 위해 hashed_password 포함된 사용자 정보 조회
- 이메일로 사용자 정보를 조회하고, hashed_password 포함 객체로 리턴. 조회 실패 시 None
- 예외 처리는 동일하게 구성

## 3. register_user(conn, name, email, hashed_password)
```python
try:
        query = f"""
        INSERT INTO user(name, email, hashed_password)
        values ('{name}', '{email}', '{hashed_password}')        
        """
        print("query:", query)
        await conn.execute(text(query))
        await conn.commit()
```
- 신규 사용자 등록hashed_password는 이미 컨트롤러(auth.py)에서 처리되었기 때문에 그대로 저장
- 트랜잭션 처리(commit / rollback) 명확히 구분
- 중복 확인은 컨트롤러에서 먼저 처리하므로 DB unique 오류는 없음

## 4. get_session(request: Request)
```python
def get_session(request: Request):
    return request.session
```
- **세션 전체 객체(request.session)에 접근하고자 할 때 사용**
- 예시)
```python
session = get_session(request)
user_id = session.get("session_user", {}).get("id")
```

## 5. get_session_user_opt(request: Request)
```python
def get_session_user_opt(request: Request):
    if "session_user" in request.session.keys():
        return request.session["session_user"]
```
- **로그인 여부에 따라 session_user가 존재하면 반환**, 없으면 None
- 선택적 로그인 유저 정보 필요할 때 사용
- 예: 블로그 목록 페이지, 글 보기 페이지

## 6. get_session_user_prt(request: Request)
```python
def get_session_user_prt(request: Request):
    if "session_user" not in request.session.keys():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="해당 서비스는 로그인이 필요합니다.")
    return request.session["session_user"]
```
- **반드시 로그인한 사용자만 접근할 수 있어야 할 때 사용**
- session_user가 없으면 401 Unauthorized 발생
- 예: 글 작성, 수정, 삭제 등 보호된 리소스에 사용

## 7. check_valid_auth()
```python
def check_valid_auth(session_user: dict, blog_author_id:int, blog_email:str):
    if session_user is None:
        return False
    if ((session_user["id"] == blog_author_id) and (session_user["email"] == blog_email)):
        return True
    return False
```
- **로그인 사용자가 해당 리소스(블로그 글)의 소유자인지 검증**
- 블로그 수정/삭제 시 본인 확인에 사용
- 검증 기준
- session_user["id"] == blog_author_id AND session_user["email"] == blog_email

# auth.py (사용자 인증 라우터)
- 회원가입, 로그인, 로그아웃 UI 및 동작 처리
- 세션에 사용자 정보 저장 및 삭제
- auth_svc.py와 연결되어 실질적인 인증 비즈니스 로직 수행

## 1. 라우터 및 템플릿 설정
```python
router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```
- /auth 하위 경로를 모두 이 라우터에서 처리
- Jinja2 템플릿을 사용하여 HTML UI 렌더링
- bcrypt를 통해 비밀번호 암호화/검증

## 2. 암호화 관련 함수
```python
def get_hashed_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)
```
- **get_hashed_password**: 회원가입 시 비밀번호를 해시 처리
- **verify_password**: 로그인 시 비밀번호 일치 여부 확인

## 3. 회원가입 UI,POST
1. 회원가입 UI
```python
@router.get("/register")
async def register_user_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register_user.html",
        context={}
    )
```
2. 회원가입 POST
```python
@router.post("/register")
async def register_user(name: str = Form(min_length=2, max_length=100),
                        email: EmailStr = Form(...),
                        password: str = Form(min_length=2, max_length=30),
                        conn: Connection = Depends(context_get_conn)):
    
    user = await auth_svc.get_user_by_email(conn=conn, email=email)
    if user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="해당 Email은 이미 등록되어 있습니다. ")
    
    hashed_password = get_hashed_password(password)
    await auth_svc.register_user(conn=conn, name=name, email=email, 
                           hashed_password=hashed_password)
    
    return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
    
    # auth_svc.register_user_...(conn=conn, name=name, email=email, password=password)
```
- **동작 순서**
1. 사용자로부터 name,email,password 받음.
2. 이메일 중복 여부 확인 (if user is not None:)
3. 비밀번호 해시화 (get_hashed_password(pasword))
4. 사용자 등록 (auth_svc.register_user)
5. 등록 완료 후 /blogs로 리디렉션 (RedirectResponse)

## 4. 로그인 UI,POST
1. 로그인 UI
```python
@router.get("/login")
async def login_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )
```
2. 로그인 POST
```python
@router.post("/login")
async def login(request: Request,
                email: EmailStr = Form(...),
                password: str = Form(min_length=2, max_length=30),
                conn: Connection = Depends(context_get_conn)):
    # 입력 email로 db에 사용자가 등록되어 있는지 확인. 
    userpass = await auth_svc.get_userpass_by_email(conn=conn, email=email)
    if userpass is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="해당 이메일 사용자는 존재하지 않습니다.")
    
    is_correct_pw = verify_password(plain_password=password, 
                                    hashed_password=userpass.hashed_password)
    if not is_correct_pw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="등록하신 이메일과 패스워드 정보가 입력 정보와 다릅니다.")
    request.session["session_user"] = {"id": userpass.id, "name": userpass.name,
                                       "email": userpass.email} #cookie에 저장.
    #print("request.session:",request.session)
    
    return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
```
- **동작 순서**
1. 입력 이메일로 사용자+암호 정보 조회(userpass = await auth_svc.get_userpass_by_email())
2. 사용자 존재 확인 (없으면 401 에러)
3. 비밀번호 검증 (is_correct_pw = verify_password())
4. **일치 시 세션에 session_user 저장 (request.session["session_user"]={"id": userpass.id, "name":userpass.name, "email":userpass.email})**
5. /blogs로 리디렉션

## 5. 로그아웃
```python
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
```
- **request.session.clear()**로 세션을 완전히 제거
- 사용자는 더 이상 로그인 상태가 아님
- 홈으로 리디렉션

## 6. await 사용하는 이유
- `auth_svc.get_userpass_by_email()` 은 async 함수이므로, 반드시 `await`을 붙여야 함.
- 비동기 처리 함수 (`async def`)를 호출할 때는 `await` 키워드를 사용해야 I/O 처리를 기다렸다가 결과를 가져올 수 있음.


# blog_svc.py 정리
## 1. get_all_blogs()
```python
@router.get("/")
async def get_all_blogs(request: Request, conn: Connection = Depends(context_get_conn)
                        , session_user = Depends(auth_svc.get_session_user_opt)):
    all_blogs = await blog_svc.get_all_blogs(conn)
    #session이 없으면 이것만 쓴다면 오류가 난다.
    print("session_user",session_user)
    
    
    return templates.TemplateResponse(
        request = request,
        name = "index.html",
        context = {"all_blogs": all_blogs,
                   "session_user": session_user}
    )
```
- **Depends(auth_svc.get_session_user_opt)**를 통해 로그인된 사용자 정보(session_user)를 받아온다.
- 로그인하지 않은 사용자도 접근 가능한 페이지이므로, session이 없어도 동작 가능하게 opt 버전을 사용한다.
- session_user값이 None일 수도 있으므로, 템플릿에서 {% if session_user %}으로 분기처리한다.

## 2. get_blog_by_id()
```python
@router.get("/show/{id}")
async def get_blog_by_id(request: Request, id: int,
                   conn: Connection = Depends(context_get_conn)
                   , session_user = Depends(auth_svc.get_session_user_opt)):
    blog = await blog_svc.get_blog_by_id(conn, id)
    blog.content = util.newline_to_br(blog.content)

    is_valid_auth = auth_svc.check_valid_auth(session_user,
                                               blog_author_id=blog.author_id,
                                               blog_email=blog.email)
    

    return templates.TemplateResponse(
        request = request,
        name="show_blog.html",
        context = {"blog": blog,
                   "session_user": session_user,
                   "is_valid_auth":is_valid_auth}
        )
```
- 게시글의 상세보기는 로그인 없이도 가능하지만, 수정/삭제 버튼은 로그인한 사용자 + 작성자 일치 조건에서만 보이도록 session_user 활용한다.(is_valid_auth)
- 내부적으로 **auth_svc.check_valid_auth()**를 통해 session_user가 본인 글인지 확인.(확인해서 맞으면 수정, 삭제 버튼이 보이도록 함.)

## 3. create_blog_ui()
```python
@router.get("/new")
async def create_blog_ui(request: Request
                         , session_user = Depends(auth_svc.get_session_user_prt)):
    return templates.TemplateResponse(
        request = request,
        name = "new_blog.html",
        context = {}
    )
```
- **새로운 블로그 작성 화면으로 이동하는 요청은 반드시 로그인되어 있어야 함.**
- 따라서 **get_session_user_prt** 사용 -> session_user가 없으면 401 에러 발생
- 인증된 사용자만 접근 가능하게 제어하는 대표적인 예

## 4. create_blog()
```python
@router.post("/new")
async def create_blog(request: Request
                , title = Form(min_length=2, max_length=200)
                , content = Form(min_length=2, max_length=4000)
                , imagefile: UploadFile | None = File(None)
                , conn: Connection = Depends(context_get_conn)
                , session_user = Depends(auth_svc.get_session_user_prt)):
    image_loc = None
    author=session_user["name"]
    author_id=session_user["id"]
    if len(imagefile.filename.strip()) > 0:
        image_loc = await blog_svc.upload_file(author=author, imagefile=imagefile)
        await blog_svc.create_blog(conn, title=title, author_id=author_id
                         , content=content, image_loc=image_loc)
    else:
        await blog_svc.create_blog(conn, title=title, author_id=author_id
                         , content=content, image_loc=image_loc)


    return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
```
- 실제 글 작성 요청 처리.
- **로그인한 사용자의 id,name을 session_user에서 추출하여 글 작성자 정보로 사용.**
```python
author = session_user["name"]
author_id = session_user["id"]
```
- 이미지 업로드 시 디렉토리는 사용자 이름(author)을 기준으로 생성됨.

## 5. update_blog_ui() & update_blog()
```python
@router.get("/modify/{id}")
async def update_blog_ui(request: Request, id: int, conn = Depends(context_get_conn)
                         , session_user = Depends(auth_svc.get_session_user_prt)):
    blog = await blog_svc.get_blog_by_id(conn, id=id)
    is_valid_auth = auth_svc.check_valid_auth(session_user,
                                               blog_author_id=blog.author_id,
                                               blog_email=blog.email)
    
    if not is_valid_auth :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="해당 서비스는 권한이 없습니다.")

    return templates.TemplateResponse(
        request = request,
        name="modify_blog.html",
        context = {"blog": blog,
                   "session_user": session_user}
    )
```
```python
@router.put("/modify/{id}")
async def update_blog(request: Request, id: int
                , title = Form(min_length=2, max_length=200)
                , content = Form(min_length=2, max_length=4000)
                , imagefile: UploadFile | None = File(None)
                , conn: Connection = Depends(context_get_conn)
                , session_user = Depends(auth_svc.get_session_user_prt)):
    blog = await blog_svc.get_blog_by_id(conn, id=id) 
    is_valid_auth = auth_svc.check_valid_auth(session_user,
                                               blog_author_id=blog.author_id,
                                               blog_email=blog.email)
    
    if not is_valid_auth :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="해당 서비스는 권한이 없습니다.")

    image_loc = None
    author = session_user["name"]

    if len(imagefile.filename.strip()) > 0:
        image_loc = await blog_svc.upload_file(author=author, imagefile=imagefile)
        await blog_svc.update_blog(conn=conn, id=id, title=title
                             , content=content, image_loc = image_loc)
    else:
        await blog_svc.update_blog(conn=conn, id=id, title=title
                             , content=content, image_loc = image_loc)

    return RedirectResponse(f"/blogs/show/{id}", status_code=status.HTTP_302_FOUND)
```
- 두 함수 모두:
- session_user가 존재해야 함.
- 글 작성자와 현재 로그인 사용자가 일치해야 수정 가능
- **내부에서 check_valid_auth() 사용하여 권한 체크**
- 일치하지 않으면 401 에러 발생
```python
if not is_valid_auth :
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="해당 서비스는 권한이 없습니다.")
```

## 6. delete_blog()
```python
@router.delete("/delete/{id}")
async def delete_blog(request: Request, id: int
                , conn: Connection = Depends(context_get_conn)
                , session_user = Depends(auth_svc.get_session_user_prt)):
    blog = await blog_svc.get_blog_by_id(conn=conn, id=id)
    is_valid_auth = auth_svc.check_valid_auth(session_user,
                                               blog_author_id=blog.author_id,
                                               blog_email=blog.email)
    
    if not is_valid_auth :
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="해당 서비스는 권한이 없습니다.")
    await blog_svc.delete_blog(conn=conn, id=id, image_loc=blog.image_loc)
    return JSONResponse(content="메시지가 삭제되었습니다", status_code=status.HTTP_200_OK)
    # return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
```
- 블로그 삭제는 JS에서 fetch로 DELETE 요청을 보내는 구조
- **session_user가 글 작성자와 동일해야 삭제 가능**
- 삭제 요청은 fetch에서 JS confirm 창을 띄우고 진행됨.

## 7. show_json/{id}
```python
@router.get("/show_json/{id}")
async def get_blog_by_id_json(request: Request, id: int,
                   conn: Connection = Depends(context_get_conn)):
    blog = await blog_svc.get_blog_by_id(conn, id)
    blog.content = util.newline_to_br(blog.content)

    return blog
```
- session과 무관한 JSON API 제공용 endpoint
- 프론트가 필요할 경우 이 API로 게시글 정보를 가져올 수 있음.

# main.py 정리
- SessionMiddleware 등록 여부 확인
```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key="...") 
```
- FastAPI는 기본적으로 세션 기능이 없기 때문에 Starlette의 `SessionMiddleware`를 등록해야 `request.session`을 사용할 수 있음.
- 내부적으로 사용자 정보를 `Signed Cookie`로 저장하고, 매 요청마다 복호화하여 세션 정보를 제공.
- 예: 로그인 후 `request.session["session_user"]`에 사용자 정보를 저장하면, 이후 페이지 요청마다 자동으로 사용자 정보가 유지됨.


