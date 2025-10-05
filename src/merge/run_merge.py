from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Iterable
import orjson as json
from src.utils.env import load
from .utils import ClusterItem, key_for, cluster_by_fuzzy
from .merge_logic import merge_cluster

def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _iter_jsonl(path: Path) -> Iterable[Dict[str,Any]]:
    with open(path, "rb") as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except Exception:
                    continue

def _write_jsonl(path: Path, items: Iterable[Dict[str,Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "ab") as f:
        for it in items:
            f.write(json.dumps(it))
            f.write(b"\n")

def merge_for_date(date_str: str | None = None) -> str:
    cfg = load()
    date_str = date_str or _stamp()
    policy = cfg.get("merge_policy") or {}
    fuzzy_cfg = policy.get("fuzzy",{}) or {}
    fuzzy_enabled = bool(fuzzy_cfg.get("enabled", False))
    fuzzy_thr = int(fuzzy_cfg.get("token_ratio_threshold", 92))
    
    enriched_root = Path("data/processed_enriched")
    out_root = Path(policy.get("out_dir","data/merged"))
    out_root.mkdir(parents=True, exist_ok=True)
    out_path = out_root / f"{date_str}.jsonl"
    
    buckets: Dict[Tuple[str,str], List[ClusterItem]] = {}
    sources_scanned = 0
    
    for src_dir in enriched_root.glob("*"):
        in_file = src_dir / f"{date_str}.jsonl"
        if not in_file.exists():
            continue
        sources_scanned += 1
        for rec in _iter_jsonl(in_file):
            k = key_for(rec)
            item = ClusterItem(
                indicator = rec.get("indicator",""),
                indicator_type = rec.get("indicator_type",""),
                record = rec,
                source = rec.get("source") or src_dir.name,
                first_seen = rec.get("first_seen"),
                last_seen = rec.get("last_seen")
            )
            buckets.setdefault(k, []).append(item)
    
    merged_rows: List[Dict[str,Any]] = []
    for (_indicator, itype), items in buckets.items():
        if not fuzzy_enabled or len(items) == 1 or itype not in ("domain","url"):
            merged_rows.append(merge_cluster(items, policy))
            continue
        
        groups = cluster_by_fuzzy(items, fuzzy_thr)
        for grp in groups:
            merged_rows.append(merge_cluster(grp, policy))
    
    _write_jsonl(out_path, merged_rows)
    
    manifest = {
        "merged_path": str(out_path),
        "date": date_str,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources_scanned": sources_scanned,
        "input_keys": len(buckets),
        "output_rows": len(merged_rows),
        "fuzzy_enabled": fuzzy_enabled,
        "fuzzy_threshold": fuzzy_thr
    }
    (out_root / f"{date_str}.manifest.json").write_bytes(json.dumps(manifest))
    
    print(f"[ok] merged {len(merged_rows)} rows from {sources_scanned} sources -> {out_path}")
    return str(out_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        merge_for_date()
    elif len(sys.argv) == 2:
        merge_for_date(sys.argv[1])
    else:
        raise SystemExit("usage: python -m src.merge.run_merge [YYYY-MM-DD]")