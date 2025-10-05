from __future__ import annotations
import orjson as json
from pathlib import Path

def coverage(alerts_path: str, sims_path: str):
    """
    Simple coverage metric:
    - total simulated events
    - how many triggered alerts
    - list missed ones
    """
    sims = []
    with open(sims_path, "rb") as f:
        for line in f:
            if line.strip():
                sims.append(json.loads(line))
    
    if not Path(alerts_path).exists():
        alerts = []
    else:
        alerts = json.loads(Path(alerts_path).read_bytes())
    
    matched_ips = {a.get("matched") for a in alerts}
    
    total = len(sims)
    hit = sum(1 for s in sims if s.get("dst_ip") in matched_ips)
    miss = [s for s in sims if s.get("dst_ip") not in matched_ips]
    
    result = {
        "total": total,
        "hit": hit,
        "miss_count": len(miss),
        "coverage_percent": round((hit/total)*100, 2) if total > 0 else 0.0
    }
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m src.simulation.coverage <alerts.json> <sims.jsonl>")
    print(json.dumps(coverage(sys.argv[1], sys.argv[2]), option=json.OPT_INDENT_2).decode())
