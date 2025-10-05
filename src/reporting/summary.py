from __future__ import annotations
from pathlib import Path
import json # FIXED: Changed from orjson
from collections import Counter, defaultdict

def _iter_jsonl(path: Path):
    # FIXED: Changed from "rb" to "r" for text mode
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except Exception:
                    continue

def summarize(scored_path: str, feedback_path: str | None = None) -> dict:
    rows = list(_iter_jsonl(Path(scored_path)))
    bands = Counter(r.get("band", "P4") for r in rows)
    avg = defaultdict(list)
    enrich_covered = 0

    for r in rows:
        avg[r.get("band", "P4")].append(r.get("score", 0))
        if r.get("enrichment"):
            enrich_covered += 1

    out = {
        "total": len(rows),
        "bands": dict(bands),
        "avg_score": {b: sum(v)/len(v) for b, v in avg.items() if v},
        "enrichment_coverage": round(enrich_covered/len(rows), 4) if rows else 0.0
    }

    if feedback_path and Path(feedback_path).exists():
        # FIXED: Changed from read_bytes() to read_text()
        fb = json.loads(Path(feedback_path).read_text(encoding="utf-8"))
        fb_counts = Counter(x.get("decision") for x in fb)
        out["feedback"] = dict(fb_counts)

    return out

if __name__ == "__main__":
    import sys
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: python -m src.reporting.summary <scored.jsonl> [feedback.json]")
    fb = sys.argv[2] if len(sys.argv) == 3 else None
    # FIXED: Changed from orjson.dumps(...) to json.dumps(..., indent=2)
    print(json.dumps(summarize(sys.argv[1], fb), indent=2))
