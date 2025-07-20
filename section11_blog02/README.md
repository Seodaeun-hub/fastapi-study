# Section 11 - 서비스 레이어(Service Layer) 도입 및 구조 개선

# 학습 주제
- Router, Service, DB 계층 분리를 통한 코드 구조 개선
- 비즈니스 로직과 라우터의 분리 -> 유지보수, 재사용성, 테스트 용이성 향상
- 라우터는 단순히 HTTP 요청과 응답만 담당 -> DB 관련 로직은 서비스 레이어에서만 처리
- 에러 처리를 서비스 레이어에 일원화하여 코드 중복 감소

# 구조 다이어그램
graph TD
    A[클라이언트 요청] --> B[Router (blog.py)]
    B -->|HTTP Request/Response 처리| C[Service Layer (blog_svc.py)]
    C -->|비즈니스 로직 실행 및 SQL 처리| D[(Database)]
    D --> C
    C --> B
    B --> A[HTML TemplateResponse 반환]

# 섹션10 vs 섹션11의 주요 차이점
1. 구조
섹션10 : Router가 DB 쿠리, 비즈니스 로직 모두 처리
섹션11 : Service Layer 추가, Router는 단순히 서비스 호출
2. 유지 보수성
섹션10 : 수정 시 Router 코드를 직접 변경해야 함.
섹션11 : DB, 로직 수정은 Service 파일만 변경하면 됨.
3. 테스트 용이성
섹션10 : Router 테스트에 DB까지 포함됨 -> 무겁고 복잡
섹션11 : Service 레이어만 단위 테스트 가능
4. 에러 처리
섹션10 : 각 Router 함수마다 중복된 try/except 작성
섹션11 : Service 레이어에서 일괄 처리
5. 재사용성
섹션10 : 동일 로직을 여러 Router에서 중복 작성
섹션11 : Service 레이어의 함수 재사용 가능

# 기능별 상세 정리
# 1. 전체 블로그 조회 (Read All)
**변경된 이유**
- 섹션10 : Router에서 직접 SQL 실행
- 섹션11 : blog_svc.get_all_blogs()로 위임 -> Router는 단순히 HTML 반환
```python
#blog_svc.py
def get_all_blogs(conn: Connection) -> List:
    try:
        query = """
        SELECT id, title, author, content, image_loc, modified_dt FROM blog;
        """
        result = conn.execute(text(query))
        all_blogs = [BlogData(id=row.id,
              title=row.title,
              author=row.author,
              content=util.truncate_text(row.content),
              image_loc=row.image_loc, 
              modified_dt=row.modified_dt) for row in result]
        
        result.close()
        return all_blogs
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="알수없는 이유로 서비스 오류가 발생하였습니다")
```
**변경 포인트**
- DB 쿼리 로직이 서비스 레이어로 이동
- BlogData 객체로 변환 후 Router로 반환

```python
@router.get("/")
def get_all_blogs(request: Request, conn: Connection = Depends(context_get_conn)):
    all_blogs = blog_svc.get_all_blogs(conn)

    return templates.TemplateResponse(
        request = request,
        name = "index.html",
        context = {"all_blogs": all_blogs}
    )
```
**변경 포인트**
- Router는 서비스 호출 + HTML TemplateResponse만 담당
- context에 all_blogs를 넘겨주어 Jinja2에서 렌더링