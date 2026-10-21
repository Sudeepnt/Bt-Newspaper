"""URL canonicalization: strip tracking params so the same article has one key."""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {
    "fbclid", "gclid", "dclid", "msclkid", "yclid", "igshid", "mc_cid", "mc_eid",
    "ref", "ref_src", "ref_url", "cmp", "ocid", "smid", "ncid", "cid", "_ga",
    "_gl", "spm", "share", "amp", "taid", "wt_mc", "s_cid",
}
TRACKING_PREFIXES = ("utm_", "at_", "hsa_", "pk_", "mtm_")
DEFAULT_PORTS = {"http": 80, "https": 443}


def is_tracking_param(name: str) -> bool:
    n = name.lower()
    return n in TRACKING_PARAMS or n.startswith(TRACKING_PREFIXES)


def canonicalize_url(url: str) -> str:
    """Return a stable form of `url`. Raises ValueError for non-http(s) URLs."""
    parts = urlsplit((url or "").strip())
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"not an http(s) url: {url!r}")
    host = parts.hostname.lower()
    if ":" in host:  # ipv6 literal
        host = f"[{host}]"
    port = parts.port
    netloc = host if port in (None, DEFAULT_PORTS[scheme]) else f"{host}:{port}"
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"
    query = sorted(
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not is_tracking_param(k)
    )
    return urlunsplit((scheme, netloc, path, urlencode(query), ""))  # fragment dropped
