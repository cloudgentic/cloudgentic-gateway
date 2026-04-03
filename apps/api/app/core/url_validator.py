"""URL validation — block SSRF attacks on user-supplied URLs."""
import ipaddress
import re
from urllib.parse import urlparse


# Private/internal IP ranges that should never be targeted
BLOCKED_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Internal Docker service hostnames
BLOCKED_HOSTNAMES = {
    "localhost", "gateway-db", "gateway-redis", "gateway-api",
    "gateway-web", "gateway-worker", "postgres", "redis",
    "metadata.google.internal", "metadata.internal",
}

VALID_URL_PATTERN = re.compile(r"^https?://[a-zA-Z0-9]")


def validate_external_url(url: str) -> str:
    """Validate that a URL is safe for outbound requests. Raises ValueError if not."""
    parsed = urlparse(url)

    # Must be http or https
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme must be http or https, got: {parsed.scheme}")

    # Must have a hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a hostname")

    # Block internal hostnames
    if hostname.lower() in BLOCKED_HOSTNAMES:
        raise ValueError(f"URL hostname is blocked: {hostname}")

    # Block IP addresses in private ranges
    try:
        ip = ipaddress.ip_address(hostname)
        for network in BLOCKED_RANGES:
            if ip in network:
                raise ValueError(f"URL targets a private/internal IP address")
    except ValueError as e:
        if "private" in str(e) or "blocked" in str(e):
            raise
        # Not an IP address — that's fine, it's a hostname

    return url
