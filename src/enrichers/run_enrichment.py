from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Iterable
import orjson as json
from src.utils.env import load
from src.enrichers.mock_enricher import enrich_mock

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

def _unique_pairs(records: Iterable[Dict[str,Any]]) -> List[Tuple[str,str]]:
    seen = set()
    pairs = []
    for r in records:
        ind = r.get("indicator","")
        it = r.get("indicator_type","")
        if not ind or not it:
            continue
        key = (ind, it)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    return pairs

def _merge_enrichment(record: Dict[str,Any], enr_key: str, result: Dict[str,Any]):
    if not result:
        return
    enr = record.setdefault("enrichment", {})
    enr[enr_key] = result
    
    ri = record.setdefault("risk_inputs", {})
    rep = result.get("reputation")
    if rep is not None:
        ri.setdefault("reputation_signals", []).append({"source": enr_key, "value": rep})
    if result.get("categories"):
        ri.setdefault("categories", set()).update(result["categories"])

def _finalize_sets(record: Dict[str,Any]):
    ri = record.get("risk_inputs") or {}
    for k in ("categories",):
        if isinstance(ri.get(k), set):
            ri[k] = sorted(list(ri[k]))

def enrich_processed_for_date(date_str: str | None = None) -> List[str]:
    cfg = load()
    date_str = date_str or _stamp()
    out_paths: List[str] = []
    
    processed_root = Path(cfg["project"]["processed_dir"])
    enriched_root = Path("data/processed_enriched")
    enriched_root.mkdir(parents=True, exist_ok=True)
    
    for src_dir in processed_root.glob("*"):
        in_file = src_dir / f"{date_str}.jsonl"
        if not in_file.exists():
            continue
        
        records = list(_iter_jsonl(in_file))
        pairs = _unique_pairs(records)
        
        if not pairs:
            continue
        
        combined_results: Dict[Tuple[str,str], Dict[str,Any]] = {}
        for ind, itype in pairs:
            combined_results[(ind, itype)] = {}
            
            # Use mock enricher
            res = enrich_mock("mock_enricher", ind, itype)
            if res is not None:
                combined_results[(ind, itype)]["mock_enricher"] = res
        
        out_file = (enriched_root / src_dir.name)
        out_file.mkdir(parents=True, exist_ok=True)
        out_file = out_file / f"{date_str}.jsonl"
        
        merged = []
        for r in records:
            ind, itype = r.get("indicator"), r.get("indicator_type")
            extras = combined_results.get((ind, itype), {})
            for enr_key, result in extras.items():
                _merge_enrichment(r, enr_key, result)
            _finalize_sets(r)
            merged.append(r)
        
        _write_jsonl(out_file, merged)
        out_paths.append(str(out_file))
        print(f"[ok] enriched {src_dir.name}: {len(merged)} -> {out_file}")
    
    return out_paths

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        enrich_processed_for_date()
    elif len(sys.argv) == 2:
        enrich_processed_for_date(sys.argv[1])
    else:
        raise SystemExit("usage: python -m src.enrichers.run_enrichment [YYYY-MM-DD]")