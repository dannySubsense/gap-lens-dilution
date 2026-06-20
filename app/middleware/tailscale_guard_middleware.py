class TailscaleGuardMiddleware:
    ADMIN_PREFIX = "/api/v1/admin/"

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if path.startswith(self.ADMIN_PREFIX):
            client = scope.get("client")
            ip = client[0] if client else ""
            if not (ip.startswith("100.") or ip.startswith("127.")):
                await send({"type": "http.response.start", "status": 403, "headers": []})
                await send({"type": "http.response.body", "body": b"Forbidden"})
                return
        await self.app(scope, receive, send)
