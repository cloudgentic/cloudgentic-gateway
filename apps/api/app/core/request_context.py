"""Request context for capturing client IP across the request lifecycle."""
from contextvars import ContextVar

# Stores the client IP for the current request — read by audit service
_client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)


def set_client_ip(ip: str | None) -> None:
    _client_ip.set(ip)


def get_client_ip() -> str | None:
    return _client_ip.get()
