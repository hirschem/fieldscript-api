
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                # Helper to check if header is present (case-insensitive)
                def has_header(name):
                    name_bytes = name.lower().encode()
                    return any(k.lower() == name_bytes for k, _ in headers)
                if not has_header("X-Content-Type-Options"):
                    headers.append((b"x-content-type-options", b"nosniff"))
                if not has_header("Referrer-Policy"):
                    headers.append((b"referrer-policy", b"no-referrer"))
                if not has_header("X-Frame-Options"):
                    headers.append((b"x-frame-options", b"DENY"))
            await send(message)

        await self.app(scope, receive, send_wrapper)
