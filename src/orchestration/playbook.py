from __future__ import annotations
from pathlib import Path
import orjson as json

def run_playbook(alerts_path: str, out_path: str):
    """
    Simple playbook:
    - For each P1 alert, create a "ticket" entry
    - Lower bands are only logged
    """
    if not Path(alerts_path).exists():
        print(f"[playbook] No alerts file found: {alerts_path}")
        Path(out_path).write_bytes(json.dumps([]))
        return out_path
    
    alerts = json.loads(Path(alerts_path).read_bytes())
    tickets = []
    
    for a in alerts:
        matched = a.get("matched", "")
        # Create ticket for high priority
        tickets.append({
            "ticket_id": f"TCK-{len(tickets)+1:04d}",
            "indicator": matched,
            "action": "investigate",
            "status": "open",
            "priority": "high"
        })
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(json.dumps(tickets, option=json.OPT_INDENT_2))
    print(f"[playbook] created {len(tickets)} tickets -> {out_path}")
    return out_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m src.orchestration.playbook <alerts.json> <tickets.json>")
    run_playbook(sys.argv[1], sys.argv[2])
