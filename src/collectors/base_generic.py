from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time
import orjson as json
from typing import Dict, Iterable, Any, Optional
from src.utils.env import load, getenv
from src.utils import http

def _now_utc_iso():
    return datetime.now(timezone.utc).isoformat()

def _iso_days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat()

def _sleep_for_rl(req_per_min: Optional[int]):
    if req_per_min and req_per_min > 0:
        time.sleep(60.0 / float(req_per_min))

def _apply_auth(headers: Dict[str, str], auth_type: str, env_key: str, params: Dict[str, Any]) -> tuple[Dict[str,str], Dict[str,Any]]:
    if auth_type == "header":
        headers = {**headers, **http.auth_header_from_env(env_key)}
    elif auth_type == "query":
        token = getenv(env_key, "")
        if token:
            params = {**params, "apikey": token}
    return headers, params

def _write_jsonl(path: Path, items: Iterable[Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "ab") as f:
        for it in items:
            f.write(json.dumps(it))
            f.write(b"\n")

def collect_source(source_cfg: Dict[str,Any]) -> str:
    cfg = load()
    raw_dir = Path(cfg["project"]["raw_dir"])
    out_dir = raw_dir / source_cfg["key"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_file = out_dir / f"{stamp}.jsonl"
    
    base_url = source_cfg["base_url"].rstrip("/")
    rl = source_cfg.get("rate_limit", {}).get("req_per_min", None)
    
    for ep in source_cfg.get("endpoints", []):
        params = {}
        headers = {}
        
        p = ep.get("params", {})
        limit_param = p.get("limit_param")
        page_param = p.get("page_param")
        cursor_param = p.get("cursor_param")
        date_param = p.get("date_param")
        default_limit = p.get("default_limit", 200)
        lookback_days = p.get("default_lookback_days", 7)
        
        if limit_param:
            params[limit_param] = default_limit
        if date_param:
            params[date_param] = _iso_days_ago(lookback_days)
        
        headers, params = _apply_auth(headers, source_cfg.get("auth_type","none"), source_cfg.get("auth_env_key",""), params)
        
        url = f"{base_url}{ep['path']}"
        next_cursor = None
        page = 1
        
        while True:
            run_params = dict(params)
            if page_param:
                run_params[page_param] = page
            if cursor_param and next_cursor:
                run_params[cursor_param] = next_cursor
            
            r = http.get(url, params=run_params, headers={**source_cfg.get("headers", {}), **headers})
            data = r.json()
            
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("items") or data.get("results") or data.get("data") or []
                if not isinstance(items, list):
                    items = [data]
            else:
                items = [data]
            
            _write_jsonl(out_file, items)
            
            next_cursor = None
            if cursor_param and isinstance(data, dict):
                next_cursor = data.get("next_cursor") or data.get("next") or data.get("cursor")
            
            more_pages = False
            if page_param:
                more_pages = (limit_param and len(items) == default_limit)
            if cursor_param:
                more_pages = bool(next_cursor)
            
            if not more_pages:
                break
            
            page += 1
            _sleep_for_rl(rl)
    
    return str(out_file)