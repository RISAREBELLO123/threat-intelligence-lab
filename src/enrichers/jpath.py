from __future__ import annotations
from typing import Any

def get_path(obj: Any, path: str, default: Any = None) -> Any:
    """
    Resolve a dotted path like 'a.b.c' across dicts/lists.
    """
    if path is None or path == "":
        return obj
    cur = obj
    for seg in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, list) and seg.isdigit():
            idx = int(seg)
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return default
        elif isinstance(cur, dict):
            cur = cur.get(seg, default)
        else:
            return default
    return cur