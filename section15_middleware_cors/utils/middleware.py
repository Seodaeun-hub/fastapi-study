from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
#middleware는 starletts에서 가져오는게 대부분.

class DummyMiddleware(BaseHTTPMiddleware) :
    async def dispatch(self, request: Request, call_next):
        print("### request info", request.url, request.method)
        print("### request type:", type(request)) #CachedRequest (원래 request를 cached해서 request를 보낸다.(별도 복제))

        response = await call_next(request)
        return response

class MethodOverrideMiddelware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("### request url, query_params, method",
               request.url, request.query_params, request.method
              )
        if request.method == "POST":
            query = request.query_params
            if query:
                method_override = query["_method"]
                if method_override:
                    method_override = method_override.upper()
                    if method_override in ("PUT", "DELETE"):
                        request.scope["method"] = method_override
        response = await call_next(request)
        return response
        