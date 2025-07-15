#DB Connection 가져오는 로직을 모듈화 하기

from sqlalchemy import create_engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager


# database connection URL
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

#with 절 사용시 이슈 
# def context_get_conn():
#     try:
#         with engine.connect() as conn:
#             yield conn #return conn이 되면 with를 벗어나서 바로 close가 되버려서 사용할 수 가 없음
#             #그러므로 이런 방식을 사용하지 않음.
#     except SQLAlchemyError as e:
#         print(e)
#         raise e
#     finally:
#         conn.close()
#         print("###### connection yield is finished")
  
@contextmanager
def context_get_conn():
    try:
        conn = engine.connect()
        yield conn #호출하는 쪽에서 conn 가져감
    except SQLAlchemyError as e:
        print(e)
        raise e
    finally:
        conn.close() #여기서 close 하는게 일반적이다.
    

    