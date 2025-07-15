from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool

# database connection URL
DATABASE_CONN = "mysql+mysqlconnector://root:root1234@localhost:3306/blog_db"

engine = create_engine(DATABASE_CONN,echo=True, #ehco=True -> 터미널에 SQL을 출력시켜줌 ROLLBACK이라고 찍히는 것이 connection이 close 됐다는 뜻.
                       poolclass=QueuePool,
                       #poolclass=NullPool,
                       pool_size=10, max_overflow=0)

def context_execute_sleep():

    with engine.connect() as conn :
        query = "select sleep(5)"
        result = conn.execute(text(query))
        result.close()
        #conn.close()
#with절을 쓰면 conn.close()를 사용하지 않아도 자동으로 connection이 close가 된다.

for ind in range(20):
    print("loop index:", ind)
    context_execute_sleep()

print("end of loop")