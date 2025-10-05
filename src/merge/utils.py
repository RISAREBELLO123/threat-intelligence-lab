from __future__ import annotations
from typing import Dict, Tuple, Any, List
from dataclasses import dataclass
from rapidfuzz import fuzz

@dataclass
class ClusterItem:
    indicator: str
    indicator_type: str
    record: Dict[str, Any]
    source: str
    first_seen: str | None
    last_seen: str | None

def key_for(record: Dict[str, Any]) -> Tuple[str, str]:
    return (record.get("indicator",""), record.get("indicator_type",""))

def similar(a: str, b: str, threshold: int) -> bool:
    if a == b:
        return True
    if a.rstrip("/") == b.rstrip("/"):
        return True
    score = fuzz.token_sort_ratio(a, b)
    return score >= threshold

def cluster_by_fuzzy(items: List[ClusterItem], threshold: int) -> List[List[ClusterItem]]:
    groups: List[List[ClusterItem]] = []
    used = [False]*len(items)
    for i, it in enumerate(items):
        if used[i]:
            continue
        group = [it]
        used[i] = True
        for j in range(i+1, len(items)):
            if used[j]:
                continue
            if it.indicator_type != items[j].indicator_type:
                continue
            if similar(it.indicator, items[j].indicator, threshold):
                group.append(items[j])
                used[j] = True
        groups.append(group)
    return groups
