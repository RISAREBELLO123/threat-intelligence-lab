from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib, time, orjson as json
from typing import Any, Dict, List, Optional
from src.utils.env import load, getenv
from src.utils import http
from .state import load as load_state, save as save_state

# ---------- small time helpers ----------
def _utc() -> datetime:
    return datetime.now(timezone.utc)

def _iso(dt: datetime) -> str:
    return dt.isoformat()

def _ago(days:int) -> str:
    return _iso(_utc() - timedelta(days=days))

# ---------- write & hash helpers ----------
def _hash(obj: Any) -> bytes:
    """
    Hash a JSON-serializable object deterministically.
    """
    return hashlib.sha256(json.dumps(obj)).digest()

def _write_jsonl(path: Path, items: List[Any]) -> int:
    """
    Append each item as a single JSON line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "ab") as f:
        for it in items:
            f.write(json.dumps(it))
            f.write(b"\n")
    return len(items)

def _sleep_rl(rpm: Optional[int]):
    """
    Respect per-minute quotas.
    """
    if rpm and rpm > 0:
        time.sleep(60.0/float(rpm))

# ---------- main collector ----------
def collect(source_cfg: Dict[str,Any]) -> str:
    """
    Generic REST collector with pagination and auth.
    """
    cfg = load()
    raw_dir = Path(cfg["project"]["raw_dir"])
    out_dir = raw_dir / source_cfg["key"]
    stamp = _utc().strftime("%Y-%m-%d")
    out_file = out_dir / f"{stamp}.jsonl"
    
    base_url = source_cfg["base_url"].rstrip("/")
    rl = source_cfg.get("rate_limit",{}).get("req_per_min")
    
    st = load_state(source_cfg["key"])
    
    # first-run lookback
    ep0 = (source_cfg.get("endpoints") or [{}])[0]
    lookback = (ep0.get("params") or {}).get("default_lookback_days", 7)
    since = st.get("since") or _ago(lookback)
    
    # track duplicates within this run
    seen = set()
    total = 0
    newest_ts = since
    
    for ep in source_cfg.get("endpoints", []):
        p = ep.get("params", {}) or {}
        limit_param = p.get("limit_param")
        page_param = p.get("page_param")
        cursor_param= p.get("cursor_param")
        date_param = p.get("date_param")
        default_lim = p.get("default_limit", 200)
        
        # assemble params and headers
        params = {}
        if limit_param: params[limit_param] = default_lim
        if date_param: params[date_param] = since
        
        headers = dict(source_cfg.get("headers", {}) or {})
        
        if source_cfg.get("auth_type") == "header":
            headers.update(http.auth_header_from_env(source_cfg.get("auth_env_key","")))
        elif source_cfg.get("auth_type") == "query":
            tok = getenv(source_cfg.get("auth_env_key",""), "")
            if tok:
                params["api_key"] = tok
        
        url = f"{base_url}{ep['path']}"
        page = 1
        cursor = None
        
        while True:
            run_params = dict(params)
            if page_param:
                run_params[page_param] = page
            if cursor_param and cursor:
                run_params[cursor_param] = cursor
            
            r = http.get(url, params=run_params, headers=headers)
            data = r.json()
            
            # normalize incoming shape to a list
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("items") or data.get("results") or data.get("data") or []
                if not isinstance(items, list):
                    items = [data]
            else:
                items = [data]
            
            # remove duplicates
            uniq = []
            for it in items:
                h = _hash(it)
                if h not in seen:
                    seen.add(h)
                    uniq.append(it)
                
                # track freshest timestamp
                if isinstance(it, dict):
                    for k in ("last_seen","modified","updated","timestamp","date"):
                        v = it.get(k)
                        if isinstance(v, str) and v > newest_ts:
                            newest_ts = v
            
            total += _write_jsonl(out_file, uniq)
            
            # check for next page
            next_cursor = None
            if cursor_param and isinstance(data, dict):
                next_cursor = data.get("next_cursor") or data.get("next") or data.get("cursor")
            
            more_by_page = bool(page_param and len(items) == default_lim)
            more_by_cursor = bool(cursor_param and next_cursor)
            
            if not (more_by_page or more_by_cursor):
                break
            
            cursor = next_cursor if next_cursor else cursor
            page += 1
            _sleep_rl(rl)
    
    # save the latest observed timestamp
    save_state(source_cfg["key"], {"since": newest_ts or since})
    
    return str(out_file)