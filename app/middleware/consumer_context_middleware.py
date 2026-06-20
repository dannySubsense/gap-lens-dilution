from app.core.consumer_context import set_current_consumer
from app.core.consumer_resolver import ConsumerResolver


class ConsumerContextMiddleware:
    def __init__(self, app, resolver: ConsumerResolver) -> None:
        self.app = app
        self._resolver = resolver

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        ip = client[0] if client else ""
        label = self._resolver.resolve(ip)
        set_current_consumer(label)
        await self.app(scope, receive, send)
