# Section 10 - Blog 애플리케이션 개발하기(기본)

## 학습 주제
- FastAPI 기반 **기본 블로그 CRUD** 구현
- **라우터(routes) 분리** 및 URL 설계
- **템플릿(Jinja2)**을 활용한 블로그 글 렌더링
- SQLAlchemy + Pydantic 기반 DB 모델 정의

## 프로젝트 디렉토리 구조 (기본)
├── db/
│ └── database.py # DB 연결 및 세션 관리
├── routes/
│ └── blog.py # 블로그 관련 CRUD 라우터
├── schemas/
│ └── blog_schema.py # Pydantic 스키마 정의
├── templates/ # Jinja2 템플릿
│ ├── index.html # 글 목록
│ ├── new_blog.html # 새 글 작성
│ ├── modify_blog.html # 글 수정
│ └── show_blog.html # 글 상세 보기
├── utils/
│ └── util.py # 공용 함수
├── main.py # FastAPI 진입점
└── initial_data.sql # 초기 샘플 데이터

# 1.DB 초기 세팅 (initial_data.sql)
```python
create database blog_db;

drop table if exists blog;

create table blog_db.blog
(
    id integer auto_increment primary key,
    title varchar(200) not null,
    author varchar(100) not null,
    content varchar(4000) not null,
    image_loc varchar(300) null,
    modified_dt datetime not null
);

truncate table blog;

insert into blog(title, author, content, modified_dt)
values 
('FastAPI는 어떤 장점이 있는가?', '둘리', '...', now()),
('FastAPI 주요 요소는 무엇인가', '고길동', '...', now()),
('FastAPI를 어떻게 사용하면 좋을까요?', '도우넛', '...', now());

COMMIT;

select * from sys.session where db='blog_db' order by conn_id;
```

# 핵심 개념 정리

1. **blog_db 생성 및 blog 테이블 생성**
- id (PK, AUTO_INCREMENT)
- title, authorm content, image_loc(이미지 경로), modified_dt(수정일)
2. **샘플 데이터 입력**
- 이후 조회(GET) API 테스트용 초기 데이터
3. **트랜잭션 관리**
- COMMIT을 명시적으로 호출해 변경 사항을 DB에 반영
4. **참고 쿼리**
- select*from sys.session where db='blog_db';
- Connection Pool 모니터링 시 사용

# 2. DB 연결 관리 (db/database.py)
```python
from sqlalchemy import create_engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager
from fastapi import status
from fastapi.exceptions import HTTPException
from dotenv import load_dotenv
import os

#1) 환경 변수에서 DB 연결 URL 로드
load_dotenv()
DATABASE_CONN = os.getenv("DATABASE_CONN")
print("########", DATABASE_CONN)

#2) 엔진 생성: SQLAlchemy + Connection Pool 설정
engine = create_engine(DATABASE_CONN,
                       poolclass=QueuePool,
                       pool_size=10, max_overflow=0,
                       pool_recycle=300)
#3) 직접 연결 (manual close 필요)
def direct_get_conn():
    conn = None
    try:
        conn=engine.connect()
        return conn
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
#4) Context Manager 기반 자동 close  
#@contextmanager -> depends에 이미 이게 있으므로 써주지 말기
def context_get_conn():
    conn = None
    try:
        conn = engine.connect()
        yield conn 
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    finally: 
        if conn:
            conn.close()
```

# 핵심 개념 정리

1. **환경 변수 관리**
- .env 파일에서 DATABASE_CONN 읽어옴 -> 코드와 민감정보(DB URL) 분리
(.env 파일 -> DATABASE_CONN = "mysql+mysqlconnector://root:root1234@localhost:3306/blog_db")
- 유지보수 및 보안성 향상
2. **create_engine 주요 파라미터**
- QueuePool : 기본 커넥션 풀, 미리 생성된 연결을 재사용
- pool_recycle : 장시간 idle 상태에서 DB가 세션을 끊는 문제 방지
3. **direct_get_conn() vs context_get_conn()**
- **직접 연결 (direct_get_conn)**
- 단순히 conn 객체 반환
- 사용자가 반드시 conn.close() 호출 -> 누락 시 커넥션 누수 발생
- **Context Manager (context_get_conn)**
- with 문법에서 사용 가능
- with 종료시 finally에서 자동으로 conn.close() 실행
- 실무에서 Context Manager 권장
4. **예외 처리**
- DB 연결 실패시 503 에러 반환 -> 클라이언트에 "서비스 일시 중단" 알림.

# 3. FastAPI 진입점 (main.py)
```python
from fastapi import FastAPI
from routes import blog

app = FastAPI()

# Blog 관련 API 라우터 등록
app.include_router(blog.router)
```

# 핵심 개념 정리
1. **FastAPI()**
- FastAPI 인스터스 생성, 앱의 엔트리포인트
2. **라우터 등록 (include_router)**
- routes/blog.py의 모든 엔드포인트를 한 번에 등록
- blog.router 내부에서 prefix="/blogs'가 설정되어 -> 모든 URL이 /blogs로 시작.
3. **모듈화 장점**
- main.py는 앱 초기화에만 집중
- 라우팅, DB, 서비스 로직을 각각 분리 -> 유지보수 용이

# 4. 공통 설정 (라우터 및 템플릿 설정)
```python
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from db.database import direct_get_conn, context_get_conn
from sqlalchemy import text, Connection
from sqlalchemy.exc import SQLAlchemyError
from schemas.blog_schema import BlogData
from utils import util

# router 생성
router = APIRouter(prefix="/blogs", tags=["blogs"])

# Jinja2 Template 엔진 생성
templates = Jinja2Templates(directory="templates")
```

# 핵심 개념
1. **APIRouter**
- prefix="/blogs' -> 모든 API가 /blogs로 시작
- tag=["blogs"] -> 자동 문서화(Swagger UI)에서 그룹화
2. **Jinja2Templates**
- HTML 템플릿 렌더링 (동적 페이지)
- /templates 디렉토리의 .html 파일 사용
3. **DB 연결 방식**
- direct_get_conn : 직접 연결, 수동으로 close 필요
- context_get_conn : with 문과 함께 자동 close
4. **데이터 가공**
BlogData (pydantic dataclass) : DB 조회 결과를 Python 객체로 변환
-> Row를 그대로 사용하면 빠르고 간단하지만 유지보수/가독성이 낮으므로 BlogData(Python 객체)를 사용해서 명확한 데이터 구조, 템플릿/가공/확장성 용이에 도움이 된다.
util 모듈 : 텍스트 자르기, 줄바꿈 → <br> 변환

# 5. 블로그 전체 목록 조회 (Index 페이지)
```html
<h1>모든 블로그 리스트</h1>
<div><a href="/blogs/new">새로운 Blog 생성</a></div>
{% for blog in all_blogs %}
    <div>
        <h3><a href="/blogs/show/{{ blog.id }}">{{ blog.title }}</a></h3>
        <p><small>Posted on {{ blog.modified_dt }} by {{ blog.author }}</small></p>
        <p>{{ blog.content }}</p>
    </div>
{% endfor %}
```
```python
@router.get("/")
async def get_all_blogs(request: Request):
    conn = None
    try:
        conn = direct_get_conn()
        query = """
        SELECT id, title, author, content, image_loc, modified_dt FROM blog
        """
        result = conn.execute(text(query))
        all_blogs = [
            BlogData(
                id=row.id,
                title=row.title,
                author=row.author,
                content=util.truncate_text(row.content),
                image_loc=row.image_loc,
                modified_dt=row.modified_dt
            )
            for row in result
        ]
        result.close()

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"all_blogs": all_blogs}
        )
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="알 수 없는 이유로 서비스 오류가 발생하였습니다.")
    finally:
        if conn:
            conn.close()

```
# 핵심 개념
1. **조회 쿼리**
- 단순 SELECT로 모든 블로그 글 반환
- text() -> SQLAlchemy의 안전한 쿼리 실행 객체
2. **리스트 컴프리헨션으로 Pydantic 객체 생성**
- SQLAlchemy Row를 그대로 쓰지 않고 BlogData로 변환 → 템플릿에서 blog.title 식으로 직관적 접근 가능.
- util.truncate_text()로 긴 content를 150자 내외로 자르고 ....을 붙여서 깔끔하게 표시.
3. **예외 처리**
- DB 오류 : SQLAlchemyError (DB 부하, 락 등) -> 503
- 기타 오류 : Exception -> 500
4. **템플릿 렌더링**
- context={"all_blogs": all_blogs}로 Jinja2에 전달
- HTML에서는 {% for blog in all_blogs %}로 루프를 돌며 출력.
5. **주의사항**
- row.image_loc1 같은 오타는 SQLAlchemyError로 잡히지 않음 -> 기본 Exception 필요
- 반드시 conn.close()호출 (direct_get_conn() 사용)

# 6. 블로그 상세보기
```html
<h1>{{ blog.title }}</h1>
<h5>Posted on {{ blog.modified_dt }} by {{ blog.author }}</h5>
<h3>{{ blog.content | safe }}</h3>

<a href="/blogs">Home으로 돌아가기</a>
<a href="/blogs/modify/{{ blog.id }}">수정하기</a>
<form action="/blogs/delete/{{ blog.id }}" method="POST">
    <button>삭제하기</button>
</form>
- {{ blog.content | safe }} → DB에 저장된 줄바꿈이 <br>로 변환된 HTML 태그가 깨지지 않도록 safe 필터 적용.
```
```python
@router.get("/show/{id}")
async def get_blog_by_id(request: Request, id: int,
                         conn: Connection = Depends(context_get_conn)):
    try:
        query = """
        SELECT id, title, author, content, image_loc, modified_dt 
        FROM blog WHERE id = :id
        """
        stmt = text(query).bindparams(id=id)
        result = conn.execute(stmt)

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"해당 id {id}는(은) 존재하지 않습니다.")

        row = result.fetchone()
        blog = BlogData(
            id=row[0],
            title=row[1],
            author=row[2],
            content=util.newline_to_br(row[3]),
            image_loc=row[4],
            modified_dt=row[5]
        )
        result.close()

        return templates.TemplateResponse(
            request=request,
            name="show_blog.html",
            context={"blog": blog}
        )
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="알 수 없는 이유로 서비스 오류가 발생하였습니다.")

```
# 핵심 개념
1. **Depends(context_get_conn)**
- FastAPI가 context_get_conn을 자동으로 호출하여 DB 연결 전달
- with 문과 동일한 효과 -> close 자동 실행

**왜 blog에서 Depends를 쓰게 되었나?**
blog 애플리케이션은 거의 모든 API가 DB 연결이 필요하다.
만약 direct_get_conn() 방식으로 한다면 모든 API마다 try, finally 로직을 중복해서 써야한다. 그러면 중복 코드가 많아지고 실수 위험도 증가한다. 

2. **bind parameter**
- :id + bindparams() -> SQL 인젝션 방지
3. **데이터 변환**
- util.newline_to_br()를 이용해 DB의 \n을 <br>로 변환.
- 템플릿에서는 |safe를 써서 <br> 태그를 HTML로 렌더링.
4. **예외 처리**
- 데이터 없음 -> 404 반환
5. **삭제/수정 버튼:**
- RedirectResponse로 /blogs/delete/{id}, /blogs/modify/{id}에 연결됨.

# 7. 블로그 글 작성 (Create)
```html
<form action="/blogs/new" method="POST">
    <input type="text" id="title" name="title">
    <input type="text" id="author" name="author">
    <textarea name="content"></textarea>
    <button>신규 블로그 생성</button>
</form>
```
```python
# UI 페이지
@router.get("/new")
def create_blog_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new_blog.html",
        context={}
    )
```
```python
# 실제 글 등록
@router.post("/new")
def create_blog(request: Request,
                title=Form(min_length=2, max_length=200),
                author=Form(max_length=100),
                content=Form(min_length=2, max_length=4000),
                conn: Connection = Depends(context_get_conn)):
    try:
        query = f"""
        INSERT INTO blog(title, author, content, modified_dt)
        VALUES ('{title}', '{author}', '{content}', now())
        """
        conn.execute(text(query))
        conn.commit()

        return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
    except SQLAlchemyError as e:
        print(e)
        conn.rollback()  # 생략 가능 (close 시 자동 rollback)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="요청데이터가 제대로 전달되지 않았습니다.")

```
# 흐름 정리
1. **GET → UI 렌더링**: 빈 context로 단순히 입력 폼만 출력.
2. **POST → 데이터 저장**:
- Form()을 사용해 클라이언트가 입력한 title, author, content를 받음.
- bindparams()로 안전하게 쿼리 바인딩 → SQL 인젝션 방지.
- 저장 후 302 리다이렉트로 다시 /blogs 페이지로 이동.


# 핵심 개념
1. **Form 데이터 검증**
- FastAPI의 Form()으로 길이, Null 허용 여부 자동 검증
2. **트랜잭션 처리**
- 반드시 conn.commit() 필요 (INSERT/UPDATE/DELETE)
- 실패 시 rollback, 다만 close 시 자동 rollback도 동작
3. **리다이렉트**
- 등록 완료 후 /blogs로 이동 (RedirectResponse)

# 8. 글 수정 (Update)
```html
<form action="/blogs/modify/{{ id }}" method="POST">
    <input type="text" id="title" name="title" value="{{ title }}">
    <input type="text" id="author" name="author" value="{{ author }}">
    <textarea name="content">{{ content }}</textarea>
    <button>블로그 수정</button>
</form>
```
```python
# UI 페이지
@router.get("/modify/{id}")
def update_blog_ui(request: Request, id: int, conn = Depends(context_get_conn)):
    query = "SELECT id, title, author, content FROM blog WHERE id = :id"
    row = conn.execute(text(query).bindparams(id=id)).fetchone()

    return templates.TemplateResponse(
        request=request,
        name="modify_blog.html",
        context={
            "id": row.id, "title": row.title,
            "author": row.author, "content": row.content
        }
    )
```
```python
# 실제 수정
@router.post("/modify/{id}")
def update_blog(request: Request, id: int,
                title=Form(min_length=2, max_length=200),
                author=Form(max_length=100),
                content=Form(min_length=2, max_length=4000),
                conn: Connection = Depends(context_get_conn)):
    try:
        query = """
        UPDATE blog
        SET title= :title, author= :author, content= :content
        WHERE id = :id
        """
        bind_stmt = text(query).bindparams(id=id, title=title,
                                           author=author, content=content)

        result = conn.execute(bind_stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"해당 id {id}는(은) 존재하지 않습니다.")
        conn.commit()
        return RedirectResponse(f"/blogs/show/{id}", status_code=status.HTTP_302_FOUND)
```
# 흐름 정리
1. **GET → 기존 데이터 출력**:
- context에 기존 제목/작성자/내용을 담아 value로 넣음.
2. **POST → 수정 후 리다이렉트**:
- 업데이트 후 바로 해당 블로그 상세 페이지(/blogs/show/{id})로 이동.

# 핵심 개념
- **bindparams()** -> 안전한 파라미터 바인딩
- **해당 id가 없을 경우** -> 404

# 9. 글 삭제 (Delete)
- UI: show_blog.html에서 <form action="/blogs/delete/{{ blog.id }}" method="POST">

```python
@router.post("/delete/{id}")
def delete_blog(request: Request, id: int,
                conn: Connection = Depends(context_get_conn)):
    try:
        query = """
        DELETE FROM blog WHERE id = :id
        """
        bind_stmt = text(query).bindparams(id=id)
        result = conn.execute(bind_stmt)

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"해당 id {id}는(은) 존재하지 않습니다.")
        conn.commit()
        return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)

```
# 핵심 개념
- **삭제된 행(row) 체크 필수** -> result.rowcount
- 삭제 완료 후 목록 페이지로 리다이렉트

# 10. 데이터 모델 (blog_schema.py)
```python
from pydantic.dataclasses import dataclass
from datetime import datetime

@dataclass
class BlogData:
    id: int
    title: str
    author: str
    content: str
    modified_dt: datetime
    image_loc: str | None = None

```
# 핵심 개념
- **@dataclass** : 단순 데이터 전달용, 검증 불필요 (조회 시 사용)
- **왜 BaseModel 안 쓰나?**
- DB에서 가져온 데이터는 이미 검증되어 있다고 가정
- Pydantic BaseModel은 유효성 검사 비용이 발생

# 11. 유틸리티 함수 (utils/util.py)
```python
def truncate_text(text, limit=150) -> str:
    if text is not None:
        return text[:limit] + "...." if len(text) > limit else text
    return None

def newline_to_br(text_newline: str) -> str:
    if text_newline is not None:
        return text_newline.replace('\n', '<br>')
    return None

```
# 핵심 개념
- **truncate_text()** : 긴 글 요약 → 목록 페이지 최적화
- **newline_to_br()** : 줄바꿈 → <br> 변환 → HTML 표시용

# CRUD 흐름 다이어그램
flowchart TD

%% ---------- 전체 CRUD 흐름 ----------

A[사용자] -->|브라우저에서 URL 요청| B[FastAPI Router]

%% CREATE
subgraph CREATE["🟢 CREATE (신규 작성)"]
    B -->|GET /blogs/new| C1[TemplateResponse → new_blog.html]
    C1 -->|빈 입력 폼 표시| A

    A -->|폼 작성 후 Submit (POST)| C2[Form()으로 입력값 수신]
    C2 -->|INSERT SQL + conn.commit()| C3[(MySQL)]
    C3 -->|302 Redirect| B
end

%% READ
subgraph READ["🔵 READ (조회)"]
    B -->|GET /blogs| R1[SELECT SQL (전체)]
    R1 -->|BlogData 객체 변환| R2[TemplateResponse → index.html]
    R2 -->|전체 글 목록 화면| A

    B -->|GET /blogs/show/{id}| R3[SELECT SQL (단건)]
    R3 -->|BlogData + newline_to_br()| R4[TemplateResponse → show_blog.html]
    R4 -->|상세 글 보기| A
end

%% UPDATE
subgraph UPDATE["🟡 UPDATE (수정)"]
    B -->|GET /blogs/modify/{id}| U1[SELECT SQL]
    U1 -->|기존 값 context로 전달| U2[TemplateResponse → modify_blog.html]
    U2 -->|폼에 기존 데이터 표시| A

    A -->|폼 수정 후 Submit (POST)| U3[Form()으로 수정값 수신]
    U3 -->|UPDATE SQL + conn.commit()| U4[(MySQL)]
    U4 -->|302 Redirect → 상세보기| R4
end

%% DELETE
subgraph DELETE["🔴 DELETE (삭제)"]
    A -->|삭제 버튼 (POST)| D1[DELETE SQL + conn.commit()]
    D1 -->|302 Redirect| R2
end
# 정리
1. **CREATE**: GET으로는 빈 폼을 보여주고, POST로 입력받아 INSERT + commit
2. **READ**:
- 전체 목록: SELECT → BlogData 변환 → index.html
- 상세 보기: SELECT → 줄바꿈 변환 → show_blog.html
3. **UPDATE**:
- **GET**: 기존 값 SELECT 후 폼에 value로 채워줌
- **POST**: 수정된 값 UPDATE + commit
4. **DELETE**: 삭제 버튼 클릭 시 DELETE + commit

# FastAPI + HTTPException 관련 ERROR 정리
1. **503 Service Unavailable**
- 상황 : DB 부하, Connection Pool Full, SQLAlchemyError 발생

2. **404 Not Found**
- 조회/수정/삭제하려는 id가 없음 (rowcount == 0)

3. **400 Bad Request**
- Form 데이터 검증 실패, INSERT/UPDATE 시 잘못된 값 전달

4. **500 Internal Server Error**
- 예상치 못한 예외 (코드 오류, Null 처리 실패 등)