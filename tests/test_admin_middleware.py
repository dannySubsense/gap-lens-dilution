import asyncio
import pytest
from app.core.consumer_context import get_current_consumer
from app.core.consumer_resolver import ConsumerResolver
from app.middleware.consumer_context_middleware import ConsumerContextMiddleware
from app.middleware.tailscale_guard_middleware import TailscaleGuardMiddleware

_MAP = {"100.70.21.69": "danny", "100.84.163.13": "jt", "100.123.146.66": "kenny"}


def _http_scope(path="/", ip="127.0.0.1"):
    return {"type": "http", "path": path, "client": (ip, 0)}


async def _noop(scope, receive, send):
    pass


def test_consumer_context_known_ip():
    resolver = ConsumerResolver(_MAP)
    captured = []

    async def downstream(scope, receive, send):
        captured.append(get_current_consumer())

    middleware = ConsumerContextMiddleware(downstream, resolver)
    scope = _http_scope(ip="100.70.21.69")
    asyncio.run(middleware(scope, None, _noop))
    assert captured == ["danny"]


def test_consumer_context_unknown_ip():
    resolver = ConsumerResolver(_MAP)
    captured = []

    async def downstream(scope, receive, send):
        captured.append(get_current_consumer())

    middleware = ConsumerContextMiddleware(downstream, resolver)
    scope = _http_scope(ip="9.9.9.9")
    asyncio.run(middleware(scope, None, _noop))
    assert captured == ["unknown"]


def test_tailscale_guard_blocks_non_tailscale_on_admin():
    called = []

    async def downstream(scope, receive, send):
        called.append(True)

    middleware = TailscaleGuardMiddleware(downstream)
    scope = _http_scope(path="/api/v1/admin/summary", ip="1.2.3.4")
    responses = []

    async def capture_send(msg):
        responses.append(msg)

    asyncio.run(middleware(scope, None, capture_send))
    assert len(called) == 0
    assert any(r.get("status") == 403 for r in responses)


def test_tailscale_guard_passes_tailscale_on_admin():
    called = []

    async def downstream(scope, receive, send):
        called.append(True)

    middleware = TailscaleGuardMiddleware(downstream)
    scope = _http_scope(path="/api/v1/admin/summary", ip="100.70.21.69")
    asyncio.run(middleware(scope, None, _noop))
    assert len(called) == 1


def test_tailscale_guard_passes_non_admin_path():
    called = []

    async def downstream(scope, receive, send):
        called.append(True)

    middleware = TailscaleGuardMiddleware(downstream)
    scope = _http_scope(path="/api/v1/dilution/AAPL", ip="1.2.3.4")
    asyncio.run(middleware(scope, None, _noop))
    assert len(called) == 1


def test_tailscale_guard_passes_loopback():
    called = []

    async def downstream(scope, receive, send):
        called.append(True)

    middleware = TailscaleGuardMiddleware(downstream)
    scope = _http_scope(path="/api/v1/admin/usage", ip="127.0.0.1")
    asyncio.run(middleware(scope, None, _noop))
    assert len(called) == 1
