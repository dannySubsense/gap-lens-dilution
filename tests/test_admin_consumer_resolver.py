"""
Tests for ConsumerContext + ConsumerResolver — Slice 3: admin-dashboard

6 tests covering:
  - IP-to-consumer resolution for all three known Tailscale peers
  - Unknown IP fallback to "unknown"
  - ContextVar default value
  - ContextVar isolation: mutations in a copied context do not affect the parent

All IPs match the defaults in Settings.tailscale_consumer_map (config.py).
"""

from contextvars import copy_context

from app.core.consumer_context import get_current_consumer, set_current_consumer
from app.core.consumer_resolver import ConsumerResolver

# ---------------------------------------------------------------------------
# Shared fixture: resolver with the production-default IP map
# ---------------------------------------------------------------------------

_DEFAULT_MAP: dict[str, str] = {
    "100.70.21.69": "danny",
    "100.84.163.13": "jt",
    "100.123.146.66": "kenny",
}


def _resolver() -> ConsumerResolver:
    return ConsumerResolver(_DEFAULT_MAP)


# ---------------------------------------------------------------------------
# 1. Known IP — danny
# ---------------------------------------------------------------------------


def test_known_ip_danny():
    """resolve("100.70.21.69") returns "danny"."""
    assert _resolver().resolve("100.70.21.69") == "danny"


# ---------------------------------------------------------------------------
# 2. Known IP — jt
# ---------------------------------------------------------------------------


def test_known_ip_jt():
    """resolve("100.84.163.13") returns "jt"."""
    assert _resolver().resolve("100.84.163.13") == "jt"


# ---------------------------------------------------------------------------
# 3. Known IP — kenny
# ---------------------------------------------------------------------------


def test_known_ip_kenny():
    """resolve("100.123.146.66") returns "kenny"."""
    assert _resolver().resolve("100.123.146.66") == "kenny"


# ---------------------------------------------------------------------------
# 4. Unknown IP falls back to "unknown"
# ---------------------------------------------------------------------------


def test_unknown_ip_returns_unknown():
    """resolve("1.2.3.4") returns "unknown" for an IP not in the map."""
    result = _resolver().resolve("1.2.3.4")
    assert result == "unknown"


# ---------------------------------------------------------------------------
# 5. ContextVar isolation: child copy is independent of parent
# ---------------------------------------------------------------------------


def test_context_var_isolation():
    """
    Mutations to the ContextVar inside a copy_context().run() block do not
    propagate back to the parent context.

    Python's contextvars guarantee that copy_context() produces a shallow
    copy of the current context snapshot.  Writes inside the copy affect only
    that copy; the parent's ContextVar value is unchanged.
    """
    # Establish a known value in the parent context.
    token = set_current_consumer("danny")
    try:
        # Run in a *child* copy of the context.
        def mutate_and_read() -> str:
            set_current_consumer("kenny")
            return get_current_consumer()

        child_result = copy_context().run(mutate_and_read)

        # Child saw its own mutation.
        assert child_result == "kenny"

        # Parent context is unaffected.
        assert get_current_consumer() == "danny"
    finally:
        # Restore default so this test does not bleed into others.
        _consumer_ctx_reset(token)


def _consumer_ctx_reset(token) -> None:
    """Helper: reset the ContextVar to its pre-set state via the Token."""
    # Import the private var so we can reset cleanly without coupling tests
    # to implementation internals beyond the public API.
    from app.core.consumer_context import _consumer_ctx  # noqa: PLC0415

    _consumer_ctx.reset(token)


# ---------------------------------------------------------------------------
# 6. Default value is "unknown" (no set_current_consumer called)
# ---------------------------------------------------------------------------


def test_consumer_default_is_unknown():
    """
    get_current_consumer() returns "unknown" in a fresh context where
    set_current_consumer() has never been called.

    Runs inside copy_context().run() to guarantee a clean slate regardless
    of test execution order.
    """
    result = copy_context().run(get_current_consumer)
    assert result == "unknown"
