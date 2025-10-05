from __future__ import annotations
from pathlib import Path
import json # FIXED: Changed from 'orjson' to standard 'json'
import glob
import re

def _iter_jsonl(path: Path):
    # FIXED: Changed from 'rb' (read bytes) to 'r' (read text)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def run_detection(rules_dir: str, logs_path: str, alerts_out: str) -> str:
    # Collect indicators from rules
    indicators = []
    for rule in glob.glob(f"{rules_dir}/*.yaml"):
        for line in Path(rule).read_text().splitlines():
            # Looks for lines like: dst_ip: 1.2.3.4
            m = re.search(r"dst_ip:\s*(\S+)", line)
            if m:
                # Remove quotes if they exist (though not expected in Sigma template)
                indicators.append(m.group(1).strip().strip("'\"")) 

    alerts = []
    for event in _iter_jsonl(Path(logs_path)):
        ip = event.get("dst_ip")
        if ip and ip in indicators:
            # Add an identifier so we know which rule fired
            alerts.append({"event": event, "matched_ip": ip, "rule_dir": rules_dir})

    Path(alerts_out).parent.mkdir(parents=True, exist_ok=True)
    # FIXED: Changed from Path.write_bytes(orjson.dumps(..., option=orjson.OPT_INDENT_2)) 
    # to Path.write_text(json.dumps(..., indent=2))
    Path(alerts_out).write_text(json.dumps(alerts, indent=2))

    print(f"[ok] {len(alerts)} alerts fired -> {alerts_out}")
    return alerts_out

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m src.detection.mock_engine <rules_dir> <logs.jsonl> <alerts.json>")
    run_detection(sys.argv[1], sys.argv[2], sys.argv[3])
