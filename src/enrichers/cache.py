from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
import orjson as json
import hashlib

ROOT = Path("data/.cache/enrich")
ROOT.mkdir(parents=True, exist_ok=True)

def _bucket_dir(enricher_key: str) -> Path:
    p = ROOT / enricher_key
    p.mkdir(parents=True, exist_ok=True)
    return p

def _key_hash(indicator_type: str, indicator: str) -> str:
    h = hashlib.sha256(f"{indicator_type}:{indicator}".encode("utf-8")).hexdigest()
    return h

def get(enricher_key: str, indicator_type: str, indicator: str, ttl_minutes: int = 1440) -> dict | None:
    p = _bucket_dir(enricher_key) / f"{_key_hash(indicator_type, indicator)}.json"
    if not p.exists():
        return None
    doc = json.loads(p.read_bytes())
    ts = datetime.fromisoformat(doc.get("_cached_at"))
    if datetime.now(timezone.utc) - ts > timedelta(minutes=ttl_minutes):
        return None
    return doc

def put(enricher_key: str, indicator_type: str, indicator: str, payload: dict) -> None:
    p = _bucket_dir(enricher_key) / f"{_key_hash(indicator_type, indicator)}.json"
    payload = dict(payload) if isinstance(payload, dict) else {"value": payload}
    payload["_cached_at"] = datetime.now(timezone.utc).isoformat()
    payload["_key"] = {"type": indicator_type, "indicator": indicator}
    p.write_bytes(json.dumps(payload))