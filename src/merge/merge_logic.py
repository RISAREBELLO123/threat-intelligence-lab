from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .utils import ClusterItem

def _best_source_index(source: str, precedence: List[str]) -> int:
    try:
        return precedence.index(source)
    except ValueError:
        return len(precedence)

def _pick_single(field: str, items: List[ClusterItem], precedence: List[str], prefer_newest: List[str]) -> Tuple[Any, Dict[str, Any]]:
    explanation = {"field": field, "strategy": None, "candidates": []}
    
    for it in items:
        val = it.record.get(field)
        if val not in (None, "", [], {}):
            explanation["candidates"].append({
                "source": it.source,
                "value": val,
                "first_seen": it.first_seen,
                "last_seen": it.last_seen,
            })
    
    if not explanation["candidates"]:
        return None, explanation
    
    if field in prefer_newest:
        explanation["strategy"] = "prefer_newest"
        def ts_of(c):
            return c.get("last_seen") or c.get("first_seen") or ""
        winner = max(explanation["candidates"], key=ts_of)
        return winner["value"], explanation
    
    explanation["strategy"] = "source_precedence"
    def rank(c):
        return _best_source_index(c["source"], precedence)
    winner = min(explanation["candidates"], key=rank)
    return winner["value"], explanation

def _union_list(vals: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for v in vals:
        if isinstance(v, list):
            for x in v:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
        else:
            if v not in seen:
                seen.add(v)
                out.append(v)
    return out

def merge_cluster(items: List[ClusterItem], policy: Dict[str, Any]) -> Dict[str, Any]:
    precedence = policy.get("precedence", {}).get("sources", [])
    prefer_newest = policy.get("precedence", {}).get("prefer_newest", [])
    union_fields = set(policy.get("union_fields", []) or [])
    
    rep = min(items, key=lambda x: (len(x.indicator), _best_source_index(x.source, precedence)))
    
    merged: Dict[str, Any] = {
        "indicator": rep.indicator,
        "indicator_type": rep.indicator_type,
        "first_seen": None,
        "last_seen": None,
        "source": "merged",
        "lineage": [],
        "merge_rationale": {},
    }
    
    firsts = [it.first_seen for it in items if it.first_seen]
    lasts = [it.last_seen for it in items if it.last_seen]
    merged["first_seen"] = min(firsts) if firsts else None
    merged["last_seen"] = max(lasts) if lasts else None
    
    for it in items:
        merged["lineage"].append({
            "source": it.source,
            "source_event_id": it.record.get("source_event_id"),
            "raw_sha256": it.record.get("raw_sha256"),
            "first_seen": it.first_seen,
            "last_seen": it.last_seen
        })
    
    all_keys = set()
    for it in items:
        all_keys.update(it.record.keys())
    
    for k in ("indicator","indicator_type","source","source_event_id","raw_sha256","lineage","merge_rationale","risk_inputs","enrichment"):
        all_keys.discard(k)
    
    for field in sorted(all_keys):
        vals = [it.record.get(field) for it in items if it.record.get(field) not in (None, "", [], {})]
        if not vals:
            continue
        
        if field in union_fields:
            merged[field] = _union_list(vals)
            merged["merge_rationale"][field] = {"strategy": "union", "sources": [it.source for it in items if it.record.get(field)]}
            continue
        
        winner, expl = _pick_single(field, items, precedence, prefer_newest)
        if winner not in (None, "", [], {}):
            merged[field] = winner
            merged["merge_rationale"][field] = expl
    
    risk_inputs = []
    for it in items:
        v = it.record.get("risk_inputs")
        if v:
            risk_inputs.append(v)
    if risk_inputs:
        merged["risk_inputs"] = risk_inputs
    
    merged["confidence"], merged["confidence_score"], merged["confidence_details"] = _combine_confidence(items, policy)
    
    enr: Dict[str, Any] = {}
    for it in sorted(items, key=lambda x: _best_source_index(x.source, precedence)):
        e = it.record.get("enrichment") or {}
        for k, v in e.items():
            if k not in enr:
                enr[k] = v
    if enr:
        merged["enrichment"] = enr
    
    return merged

def _combine_confidence(items: List[ClusterItem], policy: Dict[str,Any]) -> Tuple[str, float, Dict[str,Any]]:
    cmap = policy.get("confidence", {}).get("normalize_map", {})
    scoremap = policy.get("confidence", {}).get("bucket_to_score", {})
    mode = policy.get("confidence", {}).get("combine", "weighted_max")
    precedence = policy.get("precedence", {}).get("sources", [])
    
    normalized: List[Tuple[str, float, str]] = []
    for it in items:
        raw = (it.record.get("confidence") or "").strip().lower()
        bucket = cmap.get(raw, cmap.get("", "medium"))
        score = scoremap.get(bucket, 0.6)
        normalized.append((bucket, score, it.source))
    
    details = {"mode": mode, "inputs": [{"source": s, "bucket": b, "score": sc} for (b,sc,s) in normalized]}
    
    if not normalized:
        return "medium", scoremap.get("medium", 0.6), details
    
    if mode == "max":
        winner = max(normalized, key=lambda t: t[1])
        return winner[0], winner[1], details
    
    def rank(tup):
        b, sc, src = tup
        return (sc, - (len(precedence) - precedence.index(src)) if src in precedence else sc)
    winner = max(normalized, key=rank)
    return winner[0], winner[1], details