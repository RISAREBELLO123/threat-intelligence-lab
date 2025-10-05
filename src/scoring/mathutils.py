from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

def days_since(ts: Optional[str]) -> float:
    if not ts:
        return float("inf")
    try:
        t = datetime.fromisoformat(ts.replace("Z","")).astimezone(timezone.utc)
    except Exception:
        return float("inf")
    return max((datetime.now(timezone.utc) - t).total_seconds() / 86400.0, 0.0)

def recency_factor(ts: Optional[str], half_life_days: float, floor: float) -> float:
    d = days_since(ts)
    if d == float("inf"):
        return floor
    base = 0.5 ** (d / max(half_life_days, 0.1))
    return max(floor, min(1.0, base))

def minmax(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    if x <= lo:
        return 0.0
    if x >= hi:
        return 1.0
    return (x - lo) / (hi - lo)

def precedence_rank(source: str, order: list) -> int:
    try:
        return order.index(source)
    except ValueError:
        return len(order)