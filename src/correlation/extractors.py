from __future__ import annotations
import re
from typing import Set, Dict, Any, List

_RE_CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
_RE_CWE = re.compile(r"\bCWE-\d{1,5}\b", re.IGNORECASE)
_RE_TID = re.compile(r"\bT\d{4}(?:\.\d{3})?\b", re.IGNORECASE)

def from_text(*fields) -> Dict[str, Set[str]]:
    cves: Set[str] = set()
    cwes: Set[str] = set()
    tids: Set[str] = set()
    
    for f in fields:
        if not f:
            continue
        for s in f:
            if not s:
                continue
            cves.update(m.upper() for m in _RE_CVE.findall(s))
            cwes.update(m.upper() for m in _RE_CWE.findall(s))
            tids.update(m.upper() for m in _RE_TID.findall(s))
    
    return {"cve": cves, "cwe": cwes, "tid": tids}

def normalize_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(v) for v in x if v not in (None, "")]
    return [str(x)]