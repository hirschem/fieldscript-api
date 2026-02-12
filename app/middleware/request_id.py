import uuid

class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return


        # Find X-Request-ID header (case-insensitive)
        headers = dict((k.decode().lower(), v.decode()) for k, v in scope.get("headers", []))
        raw_request_id = headers.get("x-request-id")
        if raw_request_id and raw_request_id.strip():
            request_id = raw_request_id.strip()
        else:
            request_id = str(uuid.uuid4())

        # Patch scope for downstream (request.state.request_id)
        # Starlette/FastAPI sets request.state.request_id from scope["state"]
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                # Remove any existing x-request-id to avoid duplicates
                filtered = [(k, v) for k, v in headers if k.lower() != b"x-request-id"]
                filtered.append((b"x-request-id", request_id.encode()))
                message["headers"] = filtered
            await send(message)

        await self.app(scope, receive, send_wrapper)
