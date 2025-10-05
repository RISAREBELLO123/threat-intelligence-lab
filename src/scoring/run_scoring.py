from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Iterable, List
import json
from datetime import datetime, timezone
from src.utils.env import load
from src.scoring.graphstats import load_graph_stats
from src.scoring.score import score_record

def _iter_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except Exception:
                    continue

def _write_jsonl(path: Path, rows: Iterable[Dict[str,Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r))
            f.write("\n")

def _indicator_node_id(rec: dict) -> str:
    return f"Indicator::Indicator|{rec.get('indicator_type','')}|{rec.get('indicator','')}"

def _band(cfg: dict, score: float) -> str:
    b = cfg["scoring"]["bands"]
    if score >= float(b["critical"]): return "P1"
    if score >= float(b["high"]): return "P2"
    if score >= float(b["medium"]): return "P3"
    return "P4"

def score_for_date(date_str: str | None = None) -> str:
    cfg = load()
    date = date_str
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    merged_path = Path((cfg.get("merge_policy") or {}).get("out_dir","data/merged")) / f"{date}.jsonl"
    if not merged_path.exists():
        raise SystemExit(f"merged file missing: {merged_path}")
    
    g_nodes = Path(cfg["correlation"]["out_dir"]) / f"{date}.nodes.json"
    g_edges = Path(cfg["correlation"]["out_dir"]) / f"{date}.edges.json"
    gstats = {}
    if g_nodes.exists() and g_edges.exists():
        gstats = load_graph_stats(str(g_nodes), str(g_edges))
    
    scored_rows: List[Dict[str,Any]] = []
    for rec in _iter_jsonl(merged_path):
        node_id = _indicator_node_id(rec)
        s, detail = score_record(cfg, rec, gstats.get(node_id))
        band = _band(cfg, s)
        
        out = dict(rec)
        out["score"] = round(s, 4)
        out["band"] = band
        out["score_breakdown"] = detail
        scored_rows.append(out)
    
    scored_rows.sort(key=lambda r: r["score"], reverse=True)
    
    budget = cfg["scoring"].get("budget", {}) or {}
    if budget.get("enabled") and isinstance(budget.get("max_alerts"), int):
        scored_rows = scored_rows[: int(budget["max_alerts"])]
    
    out_dir = Path(cfg["scoring"]["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date}.jsonl"
    _write_jsonl(out_path, scored_rows)
    
    # FIX: Changed from .write_bytes() to .write_text() to handle string output from json.dumps()
    (out_dir / f"{date}.manifest.json").write_text(json.dumps({
        "scored_path": str(out_path),
        "date": date,
        "count": len(scored_rows)
    }))
    
    print(f"[ok] scored {len(scored_rows)} rows -> {out_path}")
    return str(out_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        score_for_date()
    elif len(sys.argv) == 2:
        score_for_date(sys.argv[1])
    else:
        raise SystemExit("usage: python -m src.scoring.run_scoring [YYYY-MM-DD]")
