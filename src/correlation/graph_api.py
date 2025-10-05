from __future__ import annotations
from typing import Dict, Any, Tuple
from pathlib import Path
import math
import orjson
import networkx as nx
from datetime import datetime, timezone

class IntelGraph:
    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.G = nx.MultiDiGraph()
        self.nodespec = config["correlation"]["nodes"]
        self.edgespec = config["correlation"]["edges"]
        sc = config["correlation"]["scoring"]
        self.half_life_days = float(sc.get("half_life_days", 30))
        self.min_w = float(sc.get("min_weight", 0.2))
        self.max_w = float(sc.get("max_weight", 1.0))
    
    def _node_key(self, kind: str, attrs: Dict[str, Any]) -> Tuple[str, str]:
        spec = self.nodespec[kind]
        parts = [kind]
        for f in spec["id_fields"]:
            parts.append(str(attrs.get(f, "")).strip())
        return (spec["key"], "|".join(parts))
    
    @staticmethod
    def _to_days_since(ts: str | None) -> float:
        if not ts:
            return float("inf")
        try:
            dt = datetime.fromisoformat(ts.replace("Z","")).astimezone(timezone.utc)
        except Exception:
            return float("inf")
        delta = datetime.now(timezone.utc) - dt
        return max(delta.total_seconds() / 86400.0, 0.0)
    
    def _decay(self, last_seen: str | None) -> float:
        d = self._to_days_since(last_seen)
        if d == float("inf"):
            return self.min_w
        frac = 0.5 ** (d / self.half_life_days)
        return max(self.min_w, min(self.max_w, frac))
    
    def add_node(self, kind: str, **attrs):
        ntype, nid = self._node_key(kind, attrs)
        label = attrs.get("label") or attrs.get("name") or nid.split("|")[-1]
        payload = {"kind": kind, "label": label, **attrs}
        if (ntype, nid) in self.G:
            self.G.nodes[(ntype, nid)].update(payload)
        else:
            self.G.add_node((ntype, nid), **payload)
        return (ntype, nid)
    
    def add_edge(self, src, dst, etype: str, base: float, confidence_bucket: str | None, 
                 confidence_score: float | None, last_seen: str | None, **attrs):
        conf_factor = {"low": 0.6, "medium": 0.8, "high": 1.0}.get((confidence_bucket or "medium").lower(), 0.8)
        recency = self._decay(last_seen)
        weight = max(self.min_w, min(self.max_w, base * conf_factor * recency))
        data = {"etype": etype, "weight": weight, "conf": confidence_bucket, 
                "conf_score": confidence_score, "last_seen": last_seen, **attrs}
        self.G.add_edge(src, dst, key=etype, **data)
    
    def export(self, out_dir: Path, basename: str) -> Dict[str, str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert nodes to JSON format
        nodes = []
        for n in self.G.nodes:
            node_data = {"id": f"{n[0]}::{n[1]}", **self.G.nodes[n]}
            nodes.append(node_data)
        
        # Convert edges to JSON format
        edges = []
        for (u, v, k, d) in self.G.edges(keys=True, data=True):
            edge_data = {
                "src": f"{u[0]}::{u[1]}", 
                "dst": f"{v[0]}::{v[1]}", 
                **d
            }
            edges.append(edge_data)
        
        # Write JSON files
        nodes_json = out_dir / f"{basename}.nodes.json"
        edges_json = out_dir / f"{basename}.edges.json"
        nodes_json.write_bytes(orjson.dumps(nodes))
        edges_json.write_bytes(orjson.dumps(edges))
        
        # Write manifest
        manifest = out_dir / f"{basename}.manifest.json"
        manifest.write_bytes(orjson.dumps({
            "nodes": len(nodes), 
            "edges": len(edges),
            "created_at": datetime.now(timezone.utc).isoformat()
        }))
        
        return {"nodes": str(nodes_json), "edges": str(edges_json), "manifest": str(manifest)}