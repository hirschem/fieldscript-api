from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip non-HTTP scopes
        if request.scope.get("type") != "http":
            return await call_next(request)
        user_id = request.headers.get("x-user-id")
        project_id = request.headers.get("x-project-id")
        if user_id:
            request.state.user_id = user_id
        if project_id:
            request.state.project_id = project_id
        return await call_next(request)
