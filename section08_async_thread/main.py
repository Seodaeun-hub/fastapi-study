from fastapi import FastAPI
import asyncio #python에 내장되어있다.
import time

app = FastAPI()

#time.sleep(20) -> 20초 동안 아무것도 못하고 대기하게 된다.
# long-running I/O-bound 작업 시뮬레이션
async def long_running_task():
    # 특정 초동안 수행 시뮬레이션
    await asyncio.sleep(20) 
    return {"status": "long_running task completed"}

#비동기 함수의 선언시 async 키워드를 사용
#비동기 함수의 호출시 await 키워드 사용
#즉 await는 async로 선언된 비동기 함수에서 수행.
#예외. asyncio event loop에서 바로 호출

@app.get("/task")
async def run_task():
    result = await long_running_task()
    return result

#비동기적으로 20초동안 대기하게 되므로 다른 일을 할 수 있다.
#즉 다른 request 아래 quick을 받을 수 있다.

# @app.get("/task")
# async def run_task():
#     time.sleep(20)  #동기 방식 : multithread를 사용 (thread pool)
#     return {"status": "long_running task completed"}

@app.get("/quick")
async def quick_response():
    return {"status": "quick response"}

#thread pool
#thread를 여러개로 request,response를 동시에 처리한다. 병렬처리방식
#fastapi에서 threadpool을 적용하는 방식은 아래와 같다.
# @app.get("/task")
# def run_task():
#     time.sleep(20)  #동기 방식 : multithread를 사용 (thread pool)
#     return {"status": "long_running task completed"}

#async 방식이 수행이 될 경우는 async로 하는 것이 좋다.
#반면에 처리를 할 수 없는 경우 즉 비동기로 호출할 수 없는 경우는 multithread 기반으로 처리되어 def run_task()로 처리해야한다.

#async def 수행 함수는 비동기 Event Loop를 적용
#def 수행 함수는 ThreadPool을 적용

#그럼 quick은 어떻게 되는가?
#빠르게 돌아가는 데이터들은 큰 차이 없다.

#multiprocess일 경우
#uvicorn main:app --workers=4 --port=8081
#parent process 1개
#4개의 threadpool과 4개의 eventloop를 가지게 된다.
#Uvicorn은 `--workers` 옵션을 통해 여러 개의 워커 프로세스를 생성합니다. 
#각 워커는 별도의 파이썬 프로세스에서 실행되어 GIL의 제약을 받지 않고 여러 CPU 코어에서 병렬로 작업을 처리할 수 있게 합니다.

