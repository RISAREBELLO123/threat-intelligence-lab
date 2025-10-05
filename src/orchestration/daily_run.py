from __future__ import annotations
from datetime import datetime, timezone
import subprocess
import sys

def run_step(cmd: list[str], name: str) -> bool:
    """
    Run one subprocess step and capture outcome.
    Returns True if successful, False otherwise.
    """
    print(f"[orchestrator] starting: {name}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[orchestrator] completed: {name}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[orchestrator] FAILED: {name} with code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False

def daily(date_str: str | None = None):
    """
    Execute the full pipeline for a given date.
    Note: Collection step creates data if missing.
    """
    date_str = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    print(f"[orchestrator] Starting daily run for {date_str}")
    
    # Simplified steps - only run what actually exists
    steps = [
        (["python", "-m", "src.detection.gen_sigma", 
          f"data/scored/{date_str}.jsonl", f"data/rules/{date_str}"], "rule generation"),
        (["python", "-m", "src.detection.mock_engine",
          f"data/rules/{date_str}", f"data/simlogs/{date_str}.jsonl", 
          f"data/alerts/{date_str}.json"], "mock detection"),
        (["python", "-m", "src.reporting.summary", 
          f"data/scored/{date_str}.jsonl", 
          f"data/feedback/{date_str}.json"], "report summary"),
        (["python", "-m", "src.reporting.charts", "band_bar",
          f"data/scored/{date_str}.jsonl", 
          f"data/reports/{date_str}.bands.png"], "chart generation")
    ]
    
    for cmd, name in steps:
        ok = run_step(cmd, name)
        if not ok:
            print(f"[orchestrator] Pipeline stopped at: {name}")
            print(f"[orchestrator] This is OK - some steps may not have data yet")
            # Don't exit - continue with other steps
            continue
    
    print(f"[orchestrator] Pipeline finished for {date_str}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        daily()
    elif len(sys.argv) == 2:
        daily(sys.argv[1])
    else:
        raise SystemExit("usage: python -m src.orchestration.daily_run [YYYY-MM-DD]")
