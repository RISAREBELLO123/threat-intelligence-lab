from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Set
import orjson as json
from datetime import datetime, timezone
from src.utils.env import load
from src.correlation.graph_api import IntelGraph
from src.correlation.extractors import from_text, normalize_list

def _iter_jsonl(path: Path):
    with open(path, "rb") as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except Exception:
                    continue

def _as_set(x) -> Set[str]:
    if x is None:
        return set()
    if isinstance(x, list):
        return set(str(v) for v in x if v not in (None, ""))
    return {str(x)}

def correlate_for_date(date_str: str | None = None) -> Dict[str, str]:
    cfg = load()
    corr_cfg = cfg["correlation"]
    out_dir = Path(corr_cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    
    merged_root = Path(cfg.get("merge_policy", {}).get("out_dir", "data/merged"))
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_file = merged_root / f"{date_str}.jsonl"
    
    if not date_file.exists():
        raise SystemExit(f"merged file not found: {date_file}")
    
    g = IntelGraph(cfg)
    rules = corr_cfg.get("rules", {}) or {}
    edge_defs = corr_cfg.get("edges", {}) or {}
    
    for rec in _iter_jsonl(date_file):
        ind = rec.get("indicator")
        itype = rec.get("indicator_type")
        if not ind or not itype:
            continue
        
        n_indicator = g.add_node("indicator", indicator=ind, indicator_type=itype, label=f"{itype}:{ind}")
        
        if rules.get("attach_source", True):
            src_key = rec.get("source") or "unknown"
            n_source = g.add_node("source", source_key=src_key, label=src_key)
            g.add_edge(n_indicator, n_source, edge_defs["supplied_by"]["key"], 
                      edge_defs["supplied_by"]["base_weight"],
                      rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
        
        if rules.get("attach_references", True):
            for url in normalize_list(rec.get("references")):
                n_ref = g.add_node("reference", url=url, label=url)
                g.add_edge(n_indicator, n_ref, edge_defs["referenced_by"]["key"],
                          edge_defs["referenced_by"]["base_weight"],
                          rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
        
        if rules.get("attach_asn_geo", True):
            enr = rec.get("enrichment") or {}
            asn = None
            cc = None
            for v in enr.values():
                asn = asn or v.get("asn")
                geo = v.get("geo") or {}
                cc = cc or (geo.get("country") if isinstance(geo, dict) else None)
            if asn:
                n_asn = g.add_node("asn", asn=str(asn), label=f"AS{asn}")
                g.add_edge(n_indicator, n_asn, edge_defs["hosted_on"]["key"], 
                          edge_defs["hosted_on"]["base_weight"],
                          rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
            if cc:
                n_country = g.add_node("country", cc=str(cc).upper(), label=str(cc).upper())
                if asn:
                    g.add_edge(n_asn, n_country, edge_defs["located_in"]["key"], 
                              edge_defs["located_in"]["base_weight"],
                              rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
                else:
                    g.add_edge(n_indicator, n_country, edge_defs["located_in"]["key"], 
                              edge_defs["located_in"]["base_weight"],
                              rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
        
        if rules.get("attach_malware_families", True):
            fams = set()
            enr = rec.get("enrichment") or {}
            for v in enr.values():
                fams.update(_as_set(v.get("malware_families")))
            for name in sorted(fams):
                n_mw = g.add_node("malware", name=name, label=name)
                g.add_edge(n_indicator, n_mw, edge_defs["linked_to"]["key"], 
                          edge_defs["linked_to"]["base_weight"],
                          rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
        
        structured_cves = _as_set(rec.get("cve_ids"))
        structured_cwes = _as_set(rec.get("cwe_ids"))
        structured_tids = _as_set(rec.get("attack_ids"))
        
        parsed = from_text(
            normalize_list(rec.get("desc")),
            normalize_list(rec.get("labels"))
        ) if rules.get("parse_attack_from_text", True) else {"cve": set(), "cwe": set(), "tid": set()}
        
        cves = structured_cves | parsed["cve"] if rules.get("attach_cves", True) else set()
        cwes = structured_cwes | parsed["cwe"] if rules.get("attach_cwes", True) else set()
        tids = structured_tids | parsed["tid"] if rules.get("attach_attack_ids", True) else set()
        
        for c in sorted(cves):
            v = g.add_node("vulnerability", cve_id=c, label=c)
            g.add_edge(n_indicator, v, edge_defs["indicates"]["key"], 
                      edge_defs["indicates"]["base_weight"],
                      rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
        
        for w in sorted(cwes):
            n = g.add_node("weakness", cwe_id=w, label=w)
            g.add_edge(n_indicator, n, edge_defs["linked_to"]["key"], 
                      edge_defs["linked_to"]["base_weight"],
                      rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
        
        for t in sorted(tids):
            n = g.add_node("technique", attack_id=t, label=t)
            g.add_edge(n_indicator, n, edge_defs["linked_to"]["key"], 
                      edge_defs["linked_to"]["base_weight"],
                      rec.get("confidence"), rec.get("confidence_score"), rec.get("last_seen"))
    
    return g.export(out_dir, date_str)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print(correlate_for_date())
    elif len(sys.argv) == 2:
        print(correlate_for_date(sys.argv[1]))
    else:
        raise SystemExit("usage: python -m src.correlation.run_correlate [YYYY-MM-DD]")