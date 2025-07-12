# Section 08 - Async & Thread 실습 정리

# 학습 주제
- FastAPI에서의 async def와 def의 차이 이해

**1. async, await**
```python
from fastapi import FastAPI
import asyncio #python에 내장되어있다.
import time

app = FastAPI()

async def long_running_task():
    await asyncio.sleep(20) 
    return {"status": "long_running task completed"}

@app.get("/task")
async def run_task():
    result = await long_running_task()
    return result

@app.get("/quick")
async def quick_response():
    return {"status": "quick response"}
``` 
- 비동기 함수의 선언시 async 키워드를 사용
- 비동기 함수의 호출시 await 키워드 사용
- 즉 await는 async로 선언된 비동기 함수에서 수행. (예외: asyncio event loop에서 바로 호출)
- 비동기적으로 20초동안 대기하게 되므로 다른 일을 할 수 있다.(/quick 요청)

**2. sync방식**
```python
@app.get("/task")
async def run_task():
    time.sleep(20) 
    return {"status": "long_running task completed"}

@app.get("/quick")
async def quick_response():
    return {"status": "quick response"}
```
- 동기 방식이므로 /task가 돌아가고 20초 후에 /quick이 돌아간다.

**3. thread pool**
```python
@app.get("/task")
def run_task():
    time.sleep(20)
    return {"status": "long_running task completed"}

@app.get("/quick")
async def quick_response():
    return {"status": "quick response"}

```
- thread pool은 thread 여러 개로 request, response를 병렬방식으로 동시에 처리한다.
- def run_task로 할 경우 thread pool 방식을 사용하여 다른 thread에서 돌기 때문에 대기없이 /quick이 바로 수행될 수 있다.
- async 방식을 사용할 수 있을 경우 async를 사용하는 것이 좋다.
- 반면에 처리할 수 없는 경우 즉 비동기로 호출할 수 없는 경우는 multithread 기반으로 처리되어 def run_task()로 처리해야한다.

- quick 같이 빠르게 돌아가는 데이터들은 큰 차이가 없다.

**4. multiprocess**
- Uvicorn은 `--workers` 옵션을 통해 여러 개의 워커 프로세스를 생성합니다. 
- 각 워커는 별도의 파이썬 프로세스에서 실행되어 GIL의 제약을 받지 않고 여러 CPU 코어에서 병렬로 작업을 처리할 수 있게 합니다.
예) uvicorn main:app --workers=4 --port=8081
- terminal에 작성할 경우 parent process 1개, threadpool, eventloop 각각 4개가 생성된다.

**5. Uvicorn, Starlette, FastAIP 역할 이해**

1. Uvicorn 역할
- python 기반의 ASGI(Asynchronous Server Gateway Interface) 웹서버
- 웹서버와 파이썬 애플리케이션 간의 연동규약이며 특히 비동기 프로그래밍 수행에 초점. 비동기적 요청 처리로 많은 동시 접속을 효율적으로 처리
2. Starlette 역할
- ASGI 기반의 Lightweight, Framework/toolkit.
- 웹 애플리케이션 구현을 위한 많은 기반 컴포넌트 제공.
- FastAPI에 사용되는 많은 기능들이 Starlette에 기반.
3. FastAPI 역할
- 모던, 고성능 웹 Framework
- 즉 Starlette의 기능에 보다 다양한 편의 기능 추가.