import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.models import ErrorResponse

_rate_limit_store = {}
_RATE_LIMIT = 60
_WINDOW = 60  # seconds

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.scope.get("type") != "http":
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        now = int(time.time())
        window_start, count = _rate_limit_store.get(client_ip, (now, 0))
        if now - window_start >= _WINDOW:
            window_start, count = now, 0
        count += 1
        _rate_limit_store[client_ip] = (window_start, count)
        if count > _RATE_LIMIT:
            request_id = getattr(request.state, "request_id", "unknown")
            request.state.error_code = "RATE_LIMIT_EXCEEDED"
            resp = JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error_code="RATE_LIMIT_EXCEEDED",
                    message="Too many requests",
                    request_id=request_id
                ).model_dump()
            )
            resp.headers["x-request-id"] = request_id
            return resp
        return await call_next(request)
