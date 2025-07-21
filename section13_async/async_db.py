from sqlalchemy import text
from db.database import direct_get_conn, engine
import asyncio


async def execute_query():
    conn = await direct_get_conn()
    print("conn type:", type(conn))
    query = "select * from blog"
    stmt = text(query)
    # SQL 호출하여 CursorResult 반환. 
    result = await conn.execute(stmt) #이게 핵심. 
    # conn.execute를 client가 던지면 db에서 쿼리를 받아서 작업을 하고 response를 던진다. 
    # 이 때 await가 오래 걸리게 되는데 async로 하면 기다리지 않고 event loop에 돌려놓게 하고 다른 request를 처리할 수 있다.


    rows = result.fetchall() #여기서는 await하면 안됌.
    print(rows)
    result.close()
    await conn.rollback() # commit을 하거나 rollback 할 때는 await
    await conn.close() # close할 때 반드시 await를 처리해야한다.
    await engine.dispose()

async def main():
    await execute_query()

if __name__ == "__main__":
    asyncio.run(main()) #안에 await할 필요 없음



