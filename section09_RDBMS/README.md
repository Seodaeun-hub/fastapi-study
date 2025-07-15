# Section 09 - RDBMS 다루기 & SQLAlchemy 활용

# 학습 주제
- RDBMS 기본 동작 원리와 SQL 처리 흐름 이해
- SQLAlchemy를 활용한 DB 연동 및 데이터 조회 (create_engine()와 Connection Pool)
- Row 객체 활용법 및 fetchall(), fetchone() 차이
- DB Connection 관리 최적화 (direct_get_conn() vs @contextmanager 기반 context_get_conn() 비교)
- 바인드 변수(Bind Variable) 사용법

# **1. RDBMS 기본 & 환경 설정**
1. **RDBMS 다루기 개요**
- RDBMS는 관계형 데이터베이스로, 테이블 간 관계를 기반으로 데이터 관리
- Python에서는 주로 SQLAlchmey ORM을 사용
- DB 서버 자원 및 Client 애플리케이션의 안정적인 운영을 위해서는 Client 프로그램이 DB 서버에 접속하여 SQL을 전달하고 결과를 반환할 때 발생하는 주요 메커니즘에 대한 이해가 반드시 필요하다.
2. **MYSQL 및 Workbench 설치**
- MySQL : 실제 데이터 저장
- Workbench : GUI 클라이언트로 SQL 실행 및 테이블 관리
3. **DB 생성**
- CREATE DATABASE fastapi_blog;
4. **DB Client Driver <-> RDBMS**
- Client Application에 DB Client Driver가 있다. 이 드라이버에서 제공하는 API를 통해 RDBMS하고 서로 인터페이스하면서 데이터를 요청하고 받는 구조로 되어있다.

5. **Client 와 RDBMS의 SQL 처리 흐름 요약**
1. **Connection 요청**
- 클라이언트가 DB에 접속하기 위해 접속 요청(Connection Request)을 보냄.
- RDBMS는 사용자 정보(ID, PW 등)를 검증하고, 통과하면 세션(Session)을 생성.
- 이후, Connection 객체를 클라이언트에게 전달함.
2. **SQL 요청**
- 클라이언트가 생성된 Connection을 통해 SQL 문장을 보냄.
예) SELECT * FROM blog
3. **SQL 처리 과정 (RDBMS 내부)**
- **SQL 문장 검증**
- 문법상 올바른 SQL인지 확인 (예: SELECT, FROM 구문 체크)
- **파싱(Parsing)**
- SQL 문장을 내부 구조로 변환.
- **실행 계획(Execution Plan) 수립**
- 가장 효율적인 방법으로 데이터를 가져오기 위한 계획 수립 (인덱스 사용 여부 등).
- **SQL 실행**
- 실행 계획에 따라 실제로 데이터를 읽거나 조작함.
- **Cursor 생성**
- 결과를 순차적으로 읽을 수 있도록 커서(Cursor)라는 포인터 생성.
4. **결과 전송**
- 클라이언트가 커서를 통해 결과를 Fetch(가져오기) 요청함.
- RDBMS는 커서에 있는 결과 데이터를 클라이언트로 전송함.
5. **Connection 종료**
- 클라이언트가 Connection 종료 요청.
- RDBMS는 해당 세션을 종료하고, 세션이 사용하던 자원(메모리, 커서 등)을 정리함.

**간단한 정리**

[1] Client → RDBMS : Connection 요청

[2] RDBMS → Client : 인증 후 세션/Connection 생성

[3] Client → RDBMS : SQL 요청 (예: SELECT * FROM blog)

[4] RDBMS : SQL 검증 → 파싱 → 실행 계획 수립 → 실행 → 커서 생성

[5] Client → RDBMS : 결과 Fetch 요청

[6] RDBMS → Client : 결과 데이터 전송

[7] Client → RDBMS : Connection 종료 요청

[8] RDBMS : 세션 종료 및 자원 정리

# 2. SQL Alchemy
- SQLAlchemy는 자신만의 DB Client Driver를 가지고 있지 않음.
- 서로 다른 Driver나, 서로 다른 RDBMS더라도 공통의 DB처리 API를 기반으로 코드를 작성할 수 있다. (DB가 바뀐다고 달라지지 않음.)
- 많은 서드파티 솔루션들이 SQLAlchemy를 지원한다. (드라이버가 뭐냐에 따라 API가 계속 달라지면 다 작성하기엔 무리가 있다. 그러므로 SQL Alchemy를 사용한다.)
- pymysql, mysqlclient, mysql-connector-python 등은 MySQL과 통신하는 실질적인 드라이버이다.
- **SQLAlchemy**는 이들 위에 올라가 있는 공통 인터페이스 & ORM 도구로, DB와 관계없이 코드를 일관되게 유지할 수 있게 해준다. 즉, SQLAlchemy는 드라이버가 아니라, 드라이버 위에 올라가는 **"통합 프레임워크"**라고 보면 된다.

# 3. Connection Pool 개념과 주요 파라미터 이해
-> 안정적인 DB 자원 관리를 위한 필수 Client 코드 구성 요소
- **Connection 관리**
- 커넥션이 계속 늘어나게 된다면 메모리 영역의 세션이 계속 만들어지면서 db 서버 메모리 영역의 과부하가 올 수도 있다.
- 또한 SQL을 재활용하지않고 계속 파싱을 하게 되면 메모리영역 과부화가 올 수 있다.
- **Connection Pooling 개요**
- **Database 서버에서 Connection을 생성하는 작업은 DB 자원을 소모한다.**
- 사용자/패스워드 검증
- 사용자 권한 확인 및 설정
- 세션 메모리 할당
웹 접속만 해도 Connection이 굉장히 많기 때문에 꽤 많은 자원을 소모하게 된다. (초당 수십건)
빈번한 OLTP성 작업의 요청마다(초당 수십건) DB Connection을 생성하고 종료하는 작업은 많은 자원을 소모하여 안정적인 db 운영에 큰 영향을 미칠 수 있음.
이걸 해결하기 위해 일정 수의 Connection을 **미리 Pool에서 생성하고**, 이를 가져다 SQL을 수행 후 Connection을 종료 시키지 않고 **다시 Pool에 반환하는 기법이 Connection Pooling**

**Connection Pool의 동작**
1. client가 connection을 요청 (conn = engine.connect()

2. connection pool에서 pool에 있는 유후 connection을 전달받고

3. 작업이 끝나면 connection 반환 conn.close()

4. connection pool에서는 connection이 종료되는 것이 아닌 connection pool로 돌아간다. (재활용 가능) 잘 반환을 해야한다.

# 4. SQLAlchemy로 MySQL 데이터 조회 실습
```python
#db_basic.py
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

DATABASE_CONN = "mysql+mysqlconnector://root:root1234@127.0.0.1:3306/blog_db"

engine = create_engine(DATABASE_CONN, poolclass= QueuePool,
            pool_size=10, max_overflow=0)

try:
    conn = engine.connect()
    query = "select id, title from blog"
    stmt = text(query)

    result = conn.execute(stmt) 

    rows = result.fetchall() 
    print(rows)

    print(type(rows[0])) #<class 'sqlalchemy.engine.row.Row'>
    print(rows[0].id, rows[0].title)
    print(rows[0][0], rows[0][1])
    print(rows[0]._key_to_index)
    result.close()

except SQLAlchemyError as e:
    print(e)
finally:
    conn.close()
```
- **Queuepool** : SQLAlchemy 기본 Connection Pool -> 연결을 미리 생성해두고 재사용
- **pool_size** : 기본 유지 연결 수 (10개)
- **max_overflow** : 초과 허용 연결 수, 0이면 pool_size 이상은 생성하지 않음.
- **text()** : SQL 쿼리 문자열을 안전하게 실행하는 SQLAlchemy 객체
- **fetchcall()** : 모든 Row를 리스트로 반환
- **Row 객체:**
* row.id / row.title : 컬럼명으로 접근
* row[0] : 인덱스로 접근 가능
* **_key_to_index** : 컬럼명 <-> 인덱스 매핑 딕셔너리
- **예외 처리 필수** : DB 연결 오류 및 SQL 실행 오류 캐치
- **finally에 반드시 conn.close() 호출** -> 커넥션 풀로 반환

# 5. with 절 사용
```python
DATABASE_CONN = "mysql+mysqlconnector://root:root1234@localhost:3306/blog_db"

engine = create_engine(DATABASE_CONN,echo=True,
                       poolclass=QueuePool,
                       pool_size=10, max_overflow=0)

def context_execute_sleep():

    with engine.connect() as conn :
        query = "select sleep(5)"
        result = conn.execute(text(query))
        result.close()

for ind in range(20):
    print("loop index:", ind)
    context_execute_sleep()

print("end of loop")
```
- with절을 쓰면 conn.close()를 사용하지 않아도 자동으로 connection이 close가 된다.


# 6. DB Connection 가져오는 로직을 모듈화
* **DB 연결 로직을 함수로 모듈화**하여 재사용성 높이기
* @contextmanager를 사용해 자동 자원 반환 구현
* **직접 conn.close() 호출 vs 자동 close() 비교**

1. **DB 연결 모듈화** 
```python
#database.py
from sqlalchemy import create_engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager

DATABASE_CONN = "mysql+mysqlconnector://root:root1234@localhost:3306/blog_db"

engine = create_engine(DATABASE_CONN,
                       poolclass=QueuePool,
                       #poolclass=NullPool, # Connection Pool 사용하지 않음. 
                       pool_size=10, max_overflow=0)

def direct_get_conn():
    try:
        conn = engine.connect()
        return conn
    except SQLAlchemyError as e:
        print(e)
        raise e

@contextmanager
def context_get_conn():
    try:
        conn = engine.connect()
        yield conn 
    except SQLAlchemyError as e:
        print(e)
        raise e
    finally:
        conn.close() 
```
- **direct_get_conn() 정의** : 이 함수는 그냥 connection 객체를 반환할 뿐임으로 **close() 호출 책임은 이 함수를 호출한 쪽**에 있다. 즉, 아래 코드처럼 반드시 명시적으로 닫아줘야한다.

- **context_get_conn() 정의** : 이 함수는 @contextmanager가 붙으면, 이 함수는 Context Manager 객체로 변환된다.**with 문법은 Context Manager 객체만 쓸 수 있다.**

2.  **direct module** 
```python
#module_direct.py
from sqlalchemy import text, Connection
from sqlalchemy.exc import SQLAlchemyError
from database import direct_get_conn

def execute_query(conn: Connection):
    query = "select * from blog"
    stmt = text(query) 
    result = conn.execute(stmt)

    rows = result.fetchall()
    print(rows)
    result.close()

def execute_sleep(conn: Connection):
    query = "select sleep(5)"
    result = conn.execute(text(query))
    result.close()

for ind in range(20):
    try: 
        conn = direct_get_conn()
        execute_sleep(conn)
        print("loop index:", ind)
    except SQLAlchemyError as e:
        print(e)
    finally: 
        conn.close()
        print("connection is closed inside finally")

print("end of loop")
```
-**direct_get_conn의 장점 및 단점**
- 장점 : 코드가 단순하며, 필요한 시점에서 원하는 로직 수행 가능
- 단점 : finally에서 매번 conn.close()를 수동으로 호출해야 함. -> 누락 시 커넥션 누수 발생

3.   **context module**
```python
#module_context.py
from sqlalchemy import text, Connection
from sqlalchemy.exc import SQLAlchemyError
from database import context_get_conn

def execute_query(conn: Connection):
    query = "select * from blog"
    stmt = text(query) 
    result = conn.execute(stmt)

    rows = result.fetchall()
    print(rows)
    result.close()

def execute_sleep(conn: Connection):
    query = "select sleep(5)"
    result = conn.execute(text(query))
    result.close()

for ind in range(20):
    try: 
        with context_get_conn() as conn:
            execute_sleep(conn)
            print("loop index:", ind) 
    except SQLAlchemyError as e:
        print(e)
    finally: 
        pass
print("end of loop")
```

- **context manager 방식 (context_get_conn)의 장점**
- 장점 : with 블록 종료시 자동으로 conn.close() 실행 -> 안정성 높음,
- finally 구분 불필요, 코드 간결
- 실무 권장 방식
- **with가 실행될 때 내부적으로는 아래와 같은 동작을 한다.**
- with context_get_conn() as conn:
- 실행될 때
    1) context_get_conn()이 호출되고
    2) yield conn 이전 부분이 실행됨
    3) yield가 conn을 넘겨줌 → conn 사용
    4) finally가 실행되어 conn.close() 자동 호출

* **즉) @contextmanager는 with문과 자동 리소스 정리(finally)를 가능하게 만드는 장치라고 이해하면 된다.**

* **그렇다면 direct_get_conn()을 with문에서 못 쓰는 이유는?**
direct_get_conn()은 단순히 connection 객체를 반환하는 함수이지, context manager 프로토콜(__enter__와 __ exit__)을 구현하지 않았기 때문이다. with 문법은 자동으로 리소소를 정리해야되므로 __enter__와 __exit__가 필수이다. 즉 @contextmanager를 쓰면 이 프로토콜이 자동으로 구현돼서 with를 쓸 수 있는 것이다.

# 7. Cursor의 fetch 사용법
- fetchall() : row Set을 개별 원소로 가지는 List로 반환 (가장 많이 사용)
-> rows = [row for row in result] 이것과 같음.
- fetchone() : row Set 단일 원소 반환 (주의 해야 함.)
- fetchmany() : row Set을 개별 원소로 가지는 List로 반환

**위에 컬럼 명을 쓰고 싶을 때**
- 코드 레벨에서 컬럼명 명시화
rows = [(row.id, row.title) for row in result]
print(rows)

# 8. bind variable 사용
- SQLAlchemy에서 바인드 변수를 활용해 SQL 인젝션 방지 및 쿼리 재사용 향상
- stmt.bindparams()를 사용하여 파라미터 값을 안전하게 바인딩하는 방법

```python
from sqlalchemy import text, Connection
from sqlalchemy.exc import SQLAlchemyError
from database import direct_get_conn
from datetime import datetime

try:
    conn = direct_get_conn()

    query = "select id, title, author from blog where id = :id and author = :author \
            and modified_dt < :modified_dt"
    stmt = text(query)
    bind_stmt = stmt.bindparams(id=1, author = '둘리', modified_dt=datetime.now())  

    result = conn.execute(bind_stmt)
    rows = result.fetchall()  
    print(rows)
    result.close()
except SQLAlchemyError as e:
    print("############# ", e)
finally:
    conn.close()
```
- 쿼리 내 바인드 변수 선언 
- :id, :author, :modified_dt
- bindparams() : 파라미터를 안전하게 전달하는 SQLAlchemy의 메서드 (딕셔너리처럼 여러 값을 한 번에 매핑)

* 즉 **bindeparams()의 사용 이유**는 변수 값이 자동으로 escape 처리되어, 직접 문자열을 더하는 방식보다 안전하며 동일한 SQL에 다양한 파라미터를 바인딩하여 반복 호출할 수 있다. 마지막으로 datetime, int 등 파이썬 객체를 DB에 맞게 자동 변환해준다.


