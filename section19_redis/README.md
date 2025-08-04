# Section 19 - Redis 기반 SessionMiddleware 전환
# 학습 목표
- 기존 Cookie/SessionMiddleware 방식과 RedisSessionMiddleware의 차이 이해
- Redis를 세션 저장소로 활용하는 구조 학습
- FastAPI에서 세션 접근 방식의 변화 (request.session -> request.state.session)분석
- 보안성과 성능 측면에서 Redis 기반 Session의 장점 이해 및 코드 적용

# 왜 Redis-based Session을 사용할까?
1. **저장위치**
- 기존 SessionMiddleware (Cookie 기반) : 브라우저 내부 (session_id, 상세정보 포함)
- Redis 기반 SessionMiddleware : Redis 메모리 DB (서버 측)
2. **보안성**
- 기존 SessionMiddleware (Cookie 기반) : 낮음(JS에서 Cookie 조작 가능)
- Redis 기반 SessionMiddleware : 높음 (브라우저엔 식별자만 저장)
3. **삭제 통제**
- 기존 SessionMiddleware (Cookie 기반) : 사용자 브라우저가 주도
- Redis 기반 SessionMiddleware : 서버가 주도 (invalidate 가능)
4. **네트워크 부하**
- 기존 SessionMiddleware (Cookie 기반) : 상세 정보가 직접 전송됨.
- Redis 기반 SessionMiddleware : 식별자만 전송됨.
5. **확장성**
- 기존 SessionMiddleware (Cookie 기반) : 제한적
- Redis 기반 SessionMiddleware : 서버 확장에 유리
6. **관리 용이성**
- 기존 SessionMiddleware (Cookie 기반) : 복잡 (인코딩/디코딩 필요)
- Redis 기반 SessionMiddleware : Redis 연계로 간단

# 주요 코드 변화
## auth_svc.py - 세션 접근 방식 변경
- 기존 request.session -> Redis 기반에서는 request.state.session으로 변경됨.
```python
# 변경 전
def get_session_user_opt(request: Request):
    if "session_user" in request.session.keys():
        return request.session["session_user"]

# 변경 후
def get_session_user_opt(request: Request):
    if "session_user" in request.state.session.keys():
        return request.state.session["session_user"]

```
- state는 FastAPI의 Request 객체가 가변 상태를 저장할 수 있는 공간으로, 커스텀 미들웨어가 세션 데이터를 여기에 바인딩해둠.
- RedisSessionMiddleware가 request.state.session을 Redis에서 꺼낸 dictionary로 설정해주는 역할을 함.

## main.py - 미들웨어 등록 구조 변화
```python
# 변경 전: Cookie 기반
# from starlette.middleware.sessions import SessionMiddleware
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 변경 후: Redis 기반
from utils.middleware import RedisSessionMiddleware
app.add_middleware(RedisSessionMiddleware)
```
- 기존 Starlette의 SessionMiddleware 대신 커스텀 RedisSessionMiddleware 사용
- Redis에 session_id 기반으로 사용자 데이터를 저장/조회/삭제

## Redis의 역할과 장점 정리
- 세션 데이터가 서버 메모리에 저장되므로 빠른 응답 시간 확보 가능
- 사용자가 많아질수록 확장성과 성능 측면에서 유리함
- Redis는 다양한 데이터 타입 지원 (hash, list, set 등)
- 서버에서 세션을 통제할 수 있어 보안 강화 가능

## 예외 처리와 보안 강화
```python
except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, ...)

# Redis 세션 미들웨어에서도 세션 유효성 체크 실패 시
if "session_user" not in request.state.session.keys():
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, ...)
```
- 데이터베이스 및 세션 예외 상화에 따른 처리 강화
- 모든 입증된 접근은 반드시 세션 존재 여부로 체크

# 마지막 본 블로그 저장 기능 추가 (Session 활용) 
- 사용자가 블로그 상세 페이지(/blog/show/{id})를 볼 때 해당 게시글 ID를 세션(session_user)에 저장
- 이후 다른 페이지에서도 "마지막 본 블로그"버튼을 통해 해당 게시글로 바로 이동 가능
- 사용자의 최근 탐색 이력 저장 기능을 통해 UX 개선

## 1. blog.py -> get_blog_by_id()내 세션에 마지막 블로그 ID 저장 추가
```PYTHON
@router.get("/show/{id}")
async def get_blog_by_id(request: Request, id: int,
                   conn: Connection = Depends(context_get_conn),
                   session_user = Depends(auth_svc.get_session_user_opt)):

    blog = await blog_svc.get_blog_by_id(conn, id)
    blog.content = util.newline_to_br(blog.content)

    # 권한 확인 (자신의 글인지)
    is_valid_auth = auth_svc.check_valid_auth(session_user, 
                                              blog_author_id=blog.author_id, 
                                              blog_email=blog.email)
    
    # 추가된 부분: 세션에 마지막 본 블로그 ID 저장
    if session_user:
        session_user['lastviewed_blog_id'] = blog.id

    return templates.TemplateResponse(
        request = request,
        name = "show_blog.html",
        context = {
            "blog": blog,
            "session_user": session_user,
            "is_valid_auth": is_valid_auth
        }
    )
```
- session_user['lastviewed_blog_id']=blog.id를 통해 Redis 세션 내부에 사용자의 마지막 조회 블로그 ID가 기록됨.
- 이후 HTML 템플릿에서도 이 정보를 활용 가능

## 2. navbar.html에 메뉴 항목 추가
```python
{% if session_user and session_user['lastviewed_blog_id'] %}
<li class="nav-item">
    <a class="nav-link active" aria-current="page" href="/blogs/show/{{ session_user['lastviewed_blog_id'] }}">
        마지막 본 블로그
    </a>
</li>
{% endif %}
```
- 세션에 lastviewed_blog_id 값이 있는 경우에만 메뉴에 마지막 본 블로그 항목 노출
- 클릭 시 해당 블로그 상세 페이지로 바로 이동 가능.

- **Redis 기반 세션 저장이므로 브라우저 종료 후에도 세션 유효시간 내에는 유지됨.**
- 복잡한 로그 기록 시스템 없이 간단한 세션 활용으로 개인화된 인터페이스 제공