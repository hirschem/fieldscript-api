import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger("request_log")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        response = await call_next(request)
        latency_ms = int((time.time() - start) * 1000)
        # Set X-Request-ID if not present
        if not response.headers.get("x-request-id"):
            response.headers["x-request-id"] = request_id
        # Auth context
        auth = getattr(request.state, "auth", None)
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "request_id": request_id
        }
        if auth:
            log_data["project_id"] = getattr(auth, "project_id", None)
            log_data["api_key_id"] = getattr(auth, "api_key_id", None)
            log_data["key_fingerprint"] = getattr(auth, "key_fingerprint", None)
        # Never log Authorization or raw API key
        logger.info(log_data)
        return response
