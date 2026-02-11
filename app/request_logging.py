import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.usage import add_usage_event

logger = logging.getLogger("uvicorn.access")
logger.setLevel(logging.INFO)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Explicitly skip non-HTTP scopes (e.g., websocket, lifespan)
        if request.scope.get("type") != "http":
            return await call_next(request)
        start = time.time()
        response = None
        error_code = None
        status = "success"
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status = "error"
            status_code = 500
            error_code = getattr(request.state, "error_code", "INTERNAL_ERROR")
            raise
        finally:
            latency_ms = int((time.time() - start) * 1000)
            request_id = getattr(request.state, "request_id", "unknown")
            user_id = getattr(request.state, "user_id", None)
            project_id = getattr(request.state, "project_id", None)
            path = request.url.path
            method = request.method
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "level": "INFO",
                "request_id": request_id,
                "path": path,
                "method": method,
                "status_code": status_code,
                "latency_ms": latency_ms,
            }
            if user_id is not None:
                log_entry["user_id"] = user_id
            if project_id is not None:
                log_entry["project_id"] = project_id
            logger.info(log_entry)
            add_usage_event({
                "request_id": request_id,
                "route": path,
                "method": method,
                "status": status,
                "error_code": error_code,
                "latency_ms": latency_ms,
            })
        return response
