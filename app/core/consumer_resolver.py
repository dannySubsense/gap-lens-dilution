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
                     E.g. {"100.70.21.69": "danny", "100.84.163.13": "jt"}.
        """
        self._mapping = mapping

    def resolve(self, ip: str) -> str:
        """Return the consumer label for *ip*, or 'unknown' if not in mapping."""
        return self._mapping.get(ip, "unknown")
