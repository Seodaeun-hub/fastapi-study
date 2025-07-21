from sqlalchemy import create_engine, Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager
from fastapi import status
from fastapi.exceptions import HTTPException
from dotenv import load_dotenv
import os

# database connection URL
# DATABASE_CONN = "mysql+aiomysql://root:root1234@localhost:3306/blog_db"
load_dotenv()

DATABASE_CONN = os.getenv("DATABASE_CONN")
print("database_conn:",DATABASE_CONN)

engine: AsyncEngine = create_async_engine(DATABASE_CONN, #echo=True,
                       #queuepool 쓰지 말기. 알아서 사용됨.(오류남)
                       #poolclass=NullPool, # Connection Pool 사용하지 않음. 
                       pool_size=10, max_overflow=0,
                       pool_recycle=300)

async def direct_get_conn():
    conn = None
    try:
        conn = await engine.connect() # await, async는 짝으로 써줘야 함.
        return conn
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")

async def context_get_conn():
    conn = None
    try:
        conn = await engine.connect()
        yield conn
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    finally:
        if conn:
            await conn.close()





