from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
# database connection URL
DATABASE_CONN = "mysql+mysqlconnector://root:root1234@127.0.0.1:3306/blog_db"
# Engine 생성
engine = create_engine(DATABASE_CONN, poolclass= QueuePool,
            pool_size=10, max_overflow=0)

try:
    # Connection 얻기
    conn = engine.connect()
    # SQL 선언 및 text로 감싸기
    query = "select id, title from blog"
    stmt = text(query)

    # SQL 호출하여 CursorResult 반환.
    result = conn.execute(stmt) #result = cursor

    rows = result.fetchall() #fetchone(1건), fetchmany
    #list형으로 모든 건을 가지게 됨.
    #예 : [(1, '테스트 title 1'), (2, '테스트 title 2'), (3, '테스트 title 3'), (4, '테스트 title 4')]
    print(rows)

    print(type(rows[0])) #type은 Row
    print(rows[0].id, rows[0].title)
    print(rows[0][0], rows[0][1])
    print(rows[0]._key_to_index)
    result.close()

    #각각에서 error가 발생할 수 있는것을 SQLAlchmeyError가 잡아낸다.
except SQLAlchemyError as e:
    print(e)
finally:
    # close() 메소드 호출하여 connection 반환.
    # connection을 얻어서 sql을 던졌는데 sql이 잘못되어서 db가 client에게 커서를 안주면 finally를 하지않으면 오류가 떨어져버려서 connection이 close가 되지 않으므르 
    # 반드시 finally 써줘야 한다.
    # 만약에 pool code가 아니라면 connection이 close가 잘 마무리 되지만, pool로 돌아가게 된다.
    # 그러므로 반드시 connection을 close를 해야한다.
    conn.close()
