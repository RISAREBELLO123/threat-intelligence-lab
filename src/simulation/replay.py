from __future__ import annotations
from pathlib import Path
import orjson as json
from src.detection import mock_engine

def replay(rules_dir: str, sim_path: str, alerts_out: str):
    """
    Replay simulated events against generated rules.
    Uses the same mock_engine as real logs but with test inputs.
    """
    print(f"[replay] Running simulation: {sim_path}")
    print(f"[replay] Against rules in: {rules_dir}")
    
    result = mock_engine.run_detection(rules_dir, sim_path, alerts_out)
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -m src.simulation.replay <rules_dir> <sim.jsonl> <alerts.json>")
    replay(sys.argv[1], sys.argv[2], sys.argv[3])
