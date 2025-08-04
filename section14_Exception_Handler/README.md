# Section 14 - 예외 처리(Exception Handling)

# 학습 주제
- FastAPI에서 발생하는 예외를 체계적으로 관리하는 방법 학습
- HTTPException, RequestVlidationError의 차이 이해 및 응답 처리
- ExceptionHandler를 통해 사용자에게 보기 좋은 에러 페이지 제공
- 예외 처리를 각 라우터나 서비스에 흩뿌리지 않고 중앙 집중화
- 서비스 안정성 및 사용자 경험 향상

# 구조 다이어그램
graph TD
    A["클라이언트 요청"] --> B["Router"]
    B --> C["Service Layer"]
    C -->|"HTTPException 발생"| D["Exception Handler (exc_handler.py)"]
    C -->|"RequestValidationError 발생"| D
    D -->|"템플릿 렌더링"| E["Error HTML 페이지"]
    E --> A

# Section 13 vs Section 14 주요 차이점
1. **예외 처리 위치**
- section 13(기존 방식) : 각 Router나 Service에서 개별 처리
- section 14(예외 처리 적용) : exc_handler.py에서 일괄 처리
2. **사용자 응답**
- section 13 : JSON 또는 Python 기본 에러 메시지
- section 14 : HTML 템플릿에 메시지 담아 출력
3. **코드 중복**
- section 13 : 각 함수에 try/except 반복
- section 14 : Exception Handler로 통합
4. **사용자 경험**
- section 13 : API 응답 같아서 친숙하지 않음
- section 14 : 브라우저에 보기 좋은 에러 페이지
5. **유지 보수**
- section 13 : 변경 시 모든 함수 수정 필요
- section 14 : 예외 처리만 따로 관리 가능

# 기능별 상세 정리
## 1. main.py에서 예외 처리 등록
```python
app.add_exception_handler(StarletteHTTPException, exc_handler.custom_http_exception_handler)

app.add_exception_handler(RequestValidationError, exc_handler.validation_exception_handler)   
```
- FastAPI 앱 실행시 전역 예외 처리기 등록
- HTTPException과 RequestValidationError 각각에 대해 처리
- 모든 경로(/blogs, /api 등)에 대해 예외 발생 시 일괄 적용

## 2. exc_handler.py - 사용자 정의 예외 처리
1. **HTTPException 처리**
```python
async def custom_http_exception_handler(request:Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        request = request,
        name = "http_error.html",
        context = {
            "status_code" : exc.status_code,
            "title_message" : "불편을 드려 죄송합니다.",
            "detail" : exc.detail
        },
        status_code=exc.status_code
    )
```
- 블로그가 없는 ID 접근 시 404 오류를 사용자 친화적 메시지와 함께 출력
- template을 사용해서 HTMLResponse로 에러 던짐.
- exc.datail은 HTTPException에서 지정한 에러 메시지로, 사용자에게 어떤 문제가 발생했는지 알려주는 핵심 텍스트

2. **RequestValidationError 처리**
```python
async def validation_exception_handler(request: Request, exc : RequestValidationError):
    return templates.TemplateResponse(
        request = request,
        name = "validation_error.html",
        context = {
            "status_code" : status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title_message" : "잘못된 값을 입력하였습니다. 제목은 최소 2자 이상, 200자 미만. 내용은 최소 2자 이상, 4000자 미만입니다.",
            "detail" : exc.errors()
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    ) 
```
- 글 작성 시 제목이 너무 짧거나 빠진 경우 -> 사용자 친화적 메시지와 함께 출력

## 3. http_error.html, validation_error.html - 사용자 화면
```html
<h1 class="display-1 text-muted">{{ status_code }}</h1>
<p class="h4 mb-4">{{ title_message }}</p>
<p class="mb-4">{{ detail }}</p>
```
- Bootstrap을 활용한 보기 좋은 오류 메시지
- "이전 페이지로 돌아가기" 버튼 제공
- 사용자 경험 개선

## 4. 실제 예외 발생 위치 예시
```python
# blog_svc.py
if result.rowcount == 0:
    raise HTTPException(status_code=404, detail="존재하지 않는 블로그입니다.")
```
```python
# blog.py
title = Form(min_length=2, max_length=200) 
# 이 조건을 어기면 RequestValidationError 자동 발생
```

# 요약 - 꼭 기억해야 할 핵심
1. **ExceptionHanler 사용**
- 예외를 일괄 처리하여 코드 중복 제거
2. **사용자 정의 템플릿 변환**
- 사용자에게 보기 좋은 에러 메시지 제공
3. **StarletteHTTPException**
- FastAPI는 내부적으로 Starlette 기반이므로 이걸 핸들링
4. **RequestValidationError**
- Pydantic의 입력값 검증 실패에 대응
5. **Service 레이어는 예외 발생만 담당**
- 실제 응답 처리(렌더링)는 중아에서 수행
-> **즉 FastAPI에서의 예외 처리는 raise만 하면 끝이고 그 후의 모든 응답은 전역 ExceptHandler가 책임짐.**

