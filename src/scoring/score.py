from __future__ import annotations
from typing import Dict, Any, Tuple
from src.scoring.mathutils import recency_factor, minmax, precedence_rank

def _confidence_factor(cfg: dict, bucket: str | None) -> float:
    bucket = (bucket or "medium").lower()
    m = cfg["scoring"]["confidence"]
    return float(m.get(bucket, m.get("medium", 0.9)))

def _trust_factor(cfg: dict, source: str) -> float:
    order = (cfg.get("merge_policy") or {}).get("precedence", {}).get("sources", []) or []
    idx = precedence_rank(source, order)
    tcfg = cfg["scoring"]["trust"]
    if idx == 0:
        return float(tcfg["top_source_bonus"])
    if idx == 1:
        return float(tcfg["mid_source_bonus"])
    return float(tcfg["other_source_bonus"])

def _sig_reputation(cfg: dict, raw_value) -> Tuple[float, dict]:
    sc = cfg["scoring"]["signals"]["reputation"]
    if not sc.get("enabled", True) or raw_value is None:
        return 0.0, {"raw": None, "norm": 0.0, "contrib": 0.0}
    norm = minmax(float(raw_value), float(sc["map_min"]), float(sc["map_max"]))
    contrib = min(norm * float(sc["cap"]), float(sc["cap"]))
    return contrib, {"raw": raw_value, "norm": round(norm, 4), "contrib": round(contrib, 4)}

def _sig_categories(cfg: dict, cats) -> Tuple[float, dict]:
    s = cfg["scoring"]["signals"]["categories"]
    if not s.get("enabled", True) or not cats:
        return 0.0, {"tags": [], "contrib": 0.0}
    weights = s.get("weights", {})
    subtotal = 0.0
    details = []
    for c in cats:
        w = float(weights.get(str(c).lower(), 0.0))
        if w > 0:
            subtotal += w
            details.append({"tag": c, "w": w})
    contrib = min(subtotal, float(s["cap"]))
    return contrib, {"tags": details, "contrib": round(contrib, 4)}

def _sig_malware(cfg: dict, fams) -> Tuple[float, dict]:
    s = cfg["scoring"]["signals"]["malware_families"]
    if not s.get("enabled", True) or not fams:
        return 0.0, {"families": [], "contrib": 0.0}
    per = float(s["per_family"])
    cap = float(s["cap"])
    subtotal = per * len(fams)
    return min(subtotal, cap), {"families": list(fams), "per": per, "contrib": round(min(subtotal, cap),4)}

def _graph_signals(cfg: dict, gstats: dict) -> Tuple[float, dict]:
    gcfg = cfg["scoring"]["graph"]
    if not gcfg.get("enabled", True) or not gstats:
        return 0.0, {"contrib": 0.0}
    deg = float(gstats.get("deg_norm", 0.0))
    ttech = float(gstats.get("tech_sum_norm", 0.0))
    tcve = float(gstats.get("cve_sum_norm", 0.0))
    score = deg * float(gcfg["degree_weight"]) + ttech * float(gcfg["technique_weight"]) + tcve * float(gcfg["cve_weight"])
    contrib = min(score, float(gcfg["cap"]))
    return contrib, {
        "deg_norm": round(deg,4), "tech_sum_norm": round(ttech,4), "cve_sum_norm": round(tcve,4),
        "weights": {"deg": gcfg["degree_weight"], "tech": gcfg["technique_weight"], "cve": gcfg["cve_weight"]},
        "contrib": round(contrib,4)
    }

def score_record(cfg: dict, rec: dict, gstats: dict | None) -> Tuple[float, dict]:
    rcfg = cfg["scoring"]["recency"]
    fresh = recency_factor(rec.get("last_seen"), float(rcfg["half_life_days"]), float(rcfg["floor"]))
    confm = _confidence_factor(cfg, rec.get("confidence"))
    trust = _trust_factor(cfg, rec.get("source") or "")
    
    enr = rec.get("enrichment") or {}
    rep_raw = None
    for v in enr.values():
        if "reputation" in v:
            rep_raw = v.get("reputation")
            break
    rep_c, rep_d = _sig_reputation(cfg, rep_raw)
    
    cats = set()
    fams = set()
    for v in enr.values():
        for c in (v.get("categories") or []):
            cats.add(str(c).lower())
        for m in (v.get("malware_families") or []):
            fams.add(str(m))
    
    cat_c, cat_d = _sig_categories(cfg, cats)
    mal_c, mal_d = _sig_malware(cfg, fams)
    g_c, g_d = _graph_signals(cfg, gstats or {})
    
    base = rep_c + cat_c + mal_c + g_c
    final = max(0.0, min(1.0, base * fresh * confm * trust))
    
    breakdown = {
        "freshness_factor": round(fresh,4),
        "confidence_factor": round(confm,4),
        "trust_factor": round(trust,4),
        "signals": {
            "reputation": rep_d,
            "categories": cat_d,
            "malware": mal_d,
            "graph": g_d,
            "sum": round(base,4)
        }
    }
    return final, breakdown