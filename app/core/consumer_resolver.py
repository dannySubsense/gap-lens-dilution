"""
Consumer resolver module.

Maps a Tailscale client IP to a named consumer label using the
Settings.tailscale_consumer_map dictionary.  IPs absent from the map
resolve to "unknown".

ConsumerContextMiddleware instantiates one ConsumerResolver at startup and
calls resolve() on every inbound request.
"""


class ConsumerResolver:
    def __init__(self, mapping: dict[str, str]) -> None:
        """
        Args:
            mapping: IP-to-consumer-name dict from Settings.tailscale_consumer_map.
                     E.g. {"192.0.2.1": "user-a", "192.0.2.2": "user-b"}.
        """
        self._mapping = mapping

    def resolve(self, ip: str) -> str:
        """Return the consumer label for *ip*, or 'unknown' if not in mapping."""
        return self._mapping.get(ip, "unknown")
