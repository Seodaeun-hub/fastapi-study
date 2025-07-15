from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool

# database connection URL
DATABASE_CONN = "mysql+mysqlconnector://root:root1234@localhost:3306/blog_db"

# engine = create_engine(DATABASE_CONN) 
engine = create_engine(DATABASE_CONN, 
                       poolclass=QueuePool,
                       #poolclass=NullPool, # Connection Pool 사용하지 않음. 
                       pool_size=10, max_overflow=2 #max_overflow는 최대한으로 만들어지는 것. 2이면 12까지 쓰인다.
                       )
print("#### engine created")

def direct_execute_sleep(is_close: bool = False):
    conn = engine.connect() #connection pooling에서 가져온 connection
    query = "select sleep(5)" #sleep(5)는 mysql에서 5초간 쉬어라.
    result = conn.execute(text(query))
    # rows = result.fetchall()
    # print(rows)
    result.close()

    # 인자로 is_close가 True일 때만 connection close()
    if is_close:
        conn.close()
        print("conn closed")
        #아예 connection이 없어지는 것이 아닌 connection pool로 돌아가는 것.

for ind in range(20):
    print("loop index:", ind)
    direct_execute_sleep(is_close=True) #False를 할경우 close가 되지않아서 connection pool로 돌아가지 못하고 계속 만들어지게됨. 그러므로 반드시 close를 해야한다.


print("end of loop")


    
73200