from __future__ import annotations
from pathlib import Path
from typing import Dict
# Changed: Using standard json module for compatibility
import json
from collections import defaultdict

def load_graph_stats(nodes_path: str, edges_path: str) -> Dict[str, dict]:
    # Fixed: Changed from orjson.loads(Path(path).read_bytes()) 
    # to json.loads(Path(path).read_text()) since standard json works with text.
    nodes = json.loads(Path(nodes_path).read_text())
    edges = json.loads(Path(edges_path).read_text())
    
    ind_ids = set(n["id"] for n in nodes if n.get("kind") == "indicator")
    deg = defaultdict(float)
    tech_sum = defaultdict(float)
    cve_sum = defaultdict(float)
    
    for e in edges:
        src, dst, w = e["src"], e["dst"], float(e.get("weight", 0.0))
        if src in ind_ids:
            deg[src] += 1.0
            if "::Technique|" in dst: tech_sum[src] += w
            if "::Vulnerability|" in dst: cve_sum[src] += w
        if dst in ind_ids:
            deg[dst] += 1.0
            if "::Technique|" in src: tech_sum[dst] += w
            if "::Vulnerability|" in src: cve_sum[dst] += w
    
    def _norm(d: dict) -> dict:
        if not d:
            return {}
        vals = list(d.values())
        lo, hi = min(vals), max(vals)
        if hi == lo:
            return {k: 0.0 for k in d}
        return {k: (v - lo) / (hi - lo) for k, v in d.items()}
    
    return {
        k: {"deg_norm": _norm(deg).get(k, 0.0),
            "tech_sum_norm": _norm(tech_sum).get(k, 0.0),
            "cve_sum_norm": _norm(cve_sum).get(k, 0.0)}
        for k in ind_ids
    }
