# Section 15 - Middleware 및 CORS 설정
# 학습 주제
- FastAPI에서의 미들웨어 구조와 동작 원리 이해
- BaseHTTPMiddleware 상속을 통한 사용자 정의 Middleware 구현
- _method=PUT/DELETE 방식과 MethodOverride 적용 이해
- CORS(Cross-Origin Resource Sharing)의 동작 원리 및 실전 설정 방법 학습
- CORSMiddleware를 활용해 외부 리소스 접근 허용

# 구조 다이어그램
sequenceDiagram
    participant Client
    participant Browser
    participant FastAPI Server
    participant Middleware
    participant Router

    Client->>Browser: HTML + JS
    Browser->>Middleware: 요청 (GET/POST/PUT/DELETE)
    Middleware->>FastAPI Server: method override 처리
    FastAPI Server->>Router: 요청 위임
    Router-->>FastAPI Server: 응답 생성
    FastAPI Server-->>Client: 응답 반환

# Section 14 vs Section 15 주요 차이점
1. **핵심 기능**
- section 14 (예외 처리) : 예외 발생 시 사용자 정의 응답 반환
- section 15 (Middleware & CORS) : 요청 전/후 동작을 가로채어 선처리/후처리
2. **대상** 
- section 14 : HTTPException, ValidationError 중심
- section 15 : Request, Response, Method, Header 중심
3. **사용 목적**
- section 14 : 안정적인 에러 응답 제공
- section 15 : HTTP 흐름 제어 및 보안정책 대응
4. **코드 위치**
- section 14 : exc_handler.py 중심
- section 15 : middleware.py 중심

# 기능별 상세 정리
## 1. 사용자 정의 Middleware (MethodOverride)
```python
class MethodOverrideMiddelware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            query = request.query_params
            method_override = query.get("_method", "").upper()
            if method_override in ("PUT", "DELETE"):
                request.scope["method"] = method_override
        response = await call_next(request)
        return response
```
- **동작 원리**
- HTML form은 POST만 지원하므로, ?_method=PUT 방식으로 실제 PUT 요청처럼 처리 (즉, query string를 사용)
- request.scope["method"]=PUT로 가짜 메서드를 진짜처럼 속여 FastAPI에 전달.
- **적용 예시**
```html
<form action="/blogs/modify/{{ blog.id }}?_method=PUT" method="POST">
```
- 실제 HTML에선 method="POST"지만, 서버에서 PUT으로 처리되도록 위장 -> RESTful 라우팅 가능.

## 왜 POST를 PUT/DELETE로 바꾸는가?
- **HTML Form의 한계 때문이다.**
1. **HTML의 <form> 태그는 오직 다음 두 가지 method만 지원한다.**
- method="GET"
- method="POST"
2. **하지만 RESTful 웹서비스 설계에서는 아래와 같은 HTTP 메서드를 다양하게 사용한다.**
- 글 목록 조회 : GET
- 새 글 작성 : POST
- 글 수정 : PUT
- 글 삭제 : DELETE
3. **문제**
- 그래서 우리가 HTML form을 통해 글을 수정하거나 삭제하려면 어떤 편법이 필요하다.
4. **해결책 : _method방식과 MethodOverrideMiddleware 사용**
- HTML에서 실제로는 POST를 보내면서, 쿼리스트링으로 _method=PUT 또는 _method=DELETE를 추가해 서버에게 "나 PUT이야!"라고 알린다. 

## 2. 사용자 요청 로깅용 DummyMiddleware
```python
class DummyMiddleware(BaseHTTPMiddleware) :
    async def dispatch(self, request: Request, call_next):
        print("### request info", request.url, request.method)
        print("### request type:", type(request)) 

        response = await call_next(request)
        return response
```
- 디버깅이나 API 모니터링 목적의 미들웨어로 활용 가능.

# CORS
## 1. CORS(Cross-Orgin Resource Sharing)란?
한 웹사이트에서 다른 도메인의 서버로 요청을 보내는 것을 허용할지 말지 브라우저가 판단하는 보안 정책.
- 예)
- 내가 http://localhost:3000 (React 개발 서버)에서
http://localhost:8081/blogs/show_json/1 (FastAPI 서버)에 요청하면?
- 포트가 다름 → 다른 Origin(출처)
- → 브라우저가 "이거 보안상 안전한 요청 맞아?" 하고 막을 수 있음

## 용어 정리
- **Origin** : 프로토콜 + 도메인 + 포트 (셋 중 하나라도 다르면 다른 Origin)
- **Preflight** : 브라우저가 본 요청 전에 OPTIONS 메서드로 미리 허용 여부 확인하는 요청

## 2. 기본 동작 : 브라우저는 CORS 안되면 막음
- 브라우저는 이걸 막기 위해 다음처럼 동작한다.

1. **요청을 보내기 전에 OPTIONS 메서드로 Preflight Request(사전 요청)을 먼저 보냄**
2. **서버가 응답 헤더에 다음을 포함해야 함:**
```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type
```
-> 이걸 허용하지 않으면 브라우저는 요청을 실행조차 하지 않음.

## 3. FastAPI에서는 어떻게 해결하나?
```python
# main.py에 CORS 설정
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], # 모든 도메인 허용
    allow_methods=["*"], # 모든 HTTP 메서드 허용 
    allow_headers=["*"], # 모든 헤더 허용
    allow_credentials=True, # 쿠키 포함 허용
    max_age=-1 # Preflight 캐싱 시간
)
```
- allow_origins=["*"] : 모든 출처에서 요청 가능(실무에선 보통 "http://localhost:3000"처럼 제한함.)
- allow_methods=["*"] : GET, POST, PUT, DELETE 등 모두 허용
- allow_headers=["*"] : Content-Type, Authorization등 모든 헤더 허용
- allow_credentials=True : 인증 쿠키 허용
- max_age = -1 : Preflight 캐싱 안함.

## 4. 실제 적용된 코드 예시
```html
<script>
        const url = 'http://localhost:8081/blogs/show_json/1';

        fetch(url, {
        method: 'GET', })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            const outputElement = document.getElementById('jsonOutput');
            outputElement.textContent = JSON.stringify(data, null, 2);
        })
        .catch((error) => {
            console.error('Error:', error);
        });

    </script>
```
- 이건 현재 HTML 파일이 다른 origin(예: file://, 127.0.0.1)일 경우 브라우저가 CORS 정책 위반 여부를 검사함.
- 이 요청이 성공하려면 서버 응답 헤더에 반드시 다음 포함되어야함. : Access-Control-Allow-Origin: *
- **이걸 FastAPI가 CORSMiddleware로 자동으로 붙여주는 것.**

## 이 섹션의 핵심 요약 문장
- FastAPI에서 Middleware는 HTTP 흐름을 제어할 수 있는 강력한 도구이며, CORS는 클라이언트와 서버 간의 보안을 위한 표준 정책이다.