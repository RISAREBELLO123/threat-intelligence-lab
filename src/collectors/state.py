from __future__ import annotations
from pathlib import Path
import orjson as json
import hashlib

STATE_DIR = Path("data/.state")
STATE_DIR.mkdir(parents=True, exist_ok=True)

def _path(name: str) -> Path:
    return STATE_DIR / f"{name}.json"

def load(name: str) -> dict:
    """
    Load per-source state (e.g., {"since": "...", "cursor": "..."})
    Missing file returns an empty dict so first run falls back to lookback.
    """
    p = _path(name)
    return json.loads(p.read_bytes()) if p.exists() else {}

def save(name: str, data: dict):
    """
    Persist the newest watermark (and any auxiliary info) atomically.
    """
    _path(name).write_bytes(json.dumps(data))