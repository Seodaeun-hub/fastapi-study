from fastapi import FastAPI, HTTPException, Request, status
#Starlette에 있는 HTTPException을 사용하는걸 권장한다.
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from routes import blog
from db.database import engine
from utils.common import lifespan
from utils import exc_handler


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
#from routes import blog #위에다가 쓰게되면 main이랑 blog랑 계속 왔다갔다해서 여기에 쓸 수 있다. (templates 하나 쓸 때)
app.include_router(blog.router)

app.add_exception_handler(StarletteHTTPException, exc_handler.custom_http_exception_handler)

app.add_exception_handler(RequestValidationError, exc_handler.validation_exception_handler)   
