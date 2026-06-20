"""
Consumer context module.

Provides a ContextVar-based consumer label that propagates through the async
call chain without requiring method-signature changes.  Set once per request
by ConsumerContextMiddleware; read by UsageCaptureService.capture().
"""

import contextvars

_consumer_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "consumer", default="unknown"
)


def get_current_consumer() -> str:
    """Return the consumer label for the current async context."""
    return _consumer_ctx.get()


def set_current_consumer(consumer: str) -> contextvars.Token:
    """Set the consumer label for the current async context.

    Returns the Token produced by ContextVar.set(); callers may use it to
    reset the var if needed (e.g. in tests).
    """
    return _consumer_ctx.set(consumer)
