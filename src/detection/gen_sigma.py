from __future__ import annotations
from pathlib import Path
import orjson as json
import hashlib
import jinja2

def _jinja_env() -> jinja2.Environment:
    return jinja2.Environment(loader=jinja2.FileSystemLoader("config/detections"))

def gen_rules(scored_path: str, out_dir: str) -> list[str]:
    env = _jinja_env()
    tmpl = env.get_template("template_sigma.yaml")
    
    p = Path(scored_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    out_files = []
    
    with open(p, "rb") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            
            # Only generate rules for P1 and P2
            if row.get("band") not in ("P1", "P2"):
                continue
                
            ind = row.get("indicator")
            typ = row.get("indicator_type")
            band = row.get("band")
            
            # Create stable ID
            indicator_sha = hashlib.sha1(f"{typ}:{ind}".encode()).hexdigest()[:8]
            
            text = tmpl.render(
                indicator=ind,
                indicator_sha=indicator_sha,
                band=band
            )
            
            out_path = out / f"{typ}_{indicator_sha}.yaml"
            out_path.write_text(text)
            out_files.append(str(out_path))
    
    print(f"[ok] generated {len(out_files)} rules in {out}")
    return out_files

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m src.detection.gen_sigma <scored.jsonl> <out_dir>")
    gen_rules(sys.argv[1], sys.argv[2])
