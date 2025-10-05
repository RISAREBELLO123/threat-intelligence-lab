from __future__ import annotations
import re, hashlib
from urllib.parse import urlsplit, urlunsplit
import tldextract

# lightweight checks
_IPv4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_HEX_RE = re.compile(r"^[A-Fa-f0-9]+$")

def sha256_bytes(data: bytes) -> str:
    """Stable content hash to link normalized items back to raw lines."""
    return hashlib.sha256(data).hexdigest()

def as_ipv4(s: str) -> str | None:
    s = s.strip()
    if not _IPv4_RE.match(s):
        return None
    parts = s.split(".")
    try:
        if all(0 <= int(p) <= 255 for p in parts):
            return ".".join(str(int(p)) for p in parts)
    except ValueError:
        return None
    return None

def as_domain(s: str) -> str | None:
    s = s.strip().lower().strip(".")
    ext = tldextract.extract(s)
    if ext.domain and ext.suffix:
        return ".".join([p for p in [ext.subdomain, ext.domain, ext.suffix] if p])
    return None

def as_url(s: str) -> str | None:
    try:
        parts = urlsplit(s.strip())
        if not parts.scheme or not parts.netloc:
            return None
        host = (parts.hostname or "").lower()
        userinfo = parts.username or ""
        if parts.password:
            userinfo += ":***"
        if userinfo:
            userinfo += "@"
        port = f":{parts.port}" if parts.port and parts.port not in (80, 443) else ""
        netloc = f"{userinfo}{host}{port}"
        path = parts.path or "/"
        return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, parts.fragment))
    except Exception:
        return None

def as_hash(s: str) -> tuple[str, str] | None:
    v = s.strip().lower()
    if not _HEX_RE.match(v):
        return None
    l = len(v)
    if l == 64: return ("sha256", v)
    if l == 40: return ("sha1", v)
    if l == 32: return ("md5", v)
    return None

def infer_type(val: str) -> str:
    if as_ipv4(val): return "ipv4"
    if as_url(val): return "url"
    if as_domain(val): return "domain"
    h = as_hash(val)
    if h: return h[0]
    v = val.lower()
    if v.startswith("cve-"): return "cve"
    if v.startswith("cwe-"): return "cwe"
    if v.startswith("cpe:"): return "cpe"
    if v.startswith("as"): return "asn"
    if "@" in val: return "email"
    return "other"

def canonical_indicator(val: str, t: str | None = None) -> tuple[str, str]:
    """
    Produce (normalized_value, normalized_type).
    """
    t = t or infer_type(val)
    if t == "ipv4":
        return (as_ipv4(val) or val.strip(), "ipv4")
    if t == "url":
        return (as_url(val) or val.strip(), "url")
    if t == "domain":
        return (as_domain(val) or val.strip().lower(), "domain")
    if t in ("sha256","sha1","md5"):
        algo_val = as_hash(val)
        return ((algo_val[1] if algo_val else val.strip().lower()),
                (algo_val[0] if algo_val else infer_type(val)))
    return (val.strip(), t)