from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import orjson as json, yaml, glob
from typing import Dict, Any, Iterable, List
from src.utils.env import load
from src.normalizers.schema import StixLike
from src.normalizers.canon import canonical_indicator, sha256_bytes

def _stamp_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _iter_jsonl(path: Path) -> Iterable[Dict[str,Any]]:
    with open(path, "rb") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def _choose_first(d: Dict[str,Any], keys: List[str]) -> Any | None:
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return None

def _load_mapping(source_key: str) -> Dict[str,Any]:
    path = Path("config/mappings") / f"{source_key}.yaml"
    if not path.exists():
        raise SystemExit(f"mapping file missing: {path}")
    return yaml.safe_load(path.read_text())

def normalize_source(source_key: str, date_str: str | None = None) -> tuple[str, int]:
    cfg = load()
    raw_dir = Path(cfg["project"]["raw_dir"]) / source_key
    date_str = date_str or _stamp_date()
    
    raw_paths = sorted(Path(raw_dir).glob(f"{date_str}.jsonl"))
    if not raw_paths:
        raise SystemExit(f"no raw file found for {source_key} on {date_str}")
    
    mapping = _load_mapping(source_key)
    
    out_dir = Path(cfg["project"]["processed_dir"]) / source_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date_str}.jsonl"
    
    written = 0
    with open(out_path, "ab") as out:
        for rp in raw_paths:
            for raw in _iter_jsonl(rp):
                raw_bytes = json.dumps(raw)
                raw_hash = sha256_bytes(raw_bytes)
                
                m = mapping.get("map", {})
                indicator_val = _choose_first(raw, m.get("indicator", [])) or ""
                provider_type = _choose_first(raw, m.get("indicator_type", [])) or ""
                
                first_seen = _choose_first(raw, m.get("first_seen", []))
                last_seen = _choose_first(raw, m.get("last_seen", []))
                
                confidence = _choose_first(raw, m.get("confidence", []))
                refs = _choose_first(raw, m.get("references", [])) or []
                if isinstance(refs, str):
                    refs = [refs]
                desc = _choose_first(raw, m.get("desc", []))
                
                if mapping.get("coerce", {}).get("indicator_type") == "auto":
                    ind_norm, type_norm = canonical_indicator(indicator_val, provider_type or None)
                else:
                    ind_norm, type_norm = canonical_indicator(indicator_val, provider_type or None)
                
                if not confidence:
                    confidence = mapping.get("defaults", {}).get("confidence")
                
                extra = {}
                for k in mapping.get("pass_through", []):
                    if k in raw:
                        extra[k] = raw[k]
                
                provider_id = raw.get("id") or raw.get("uuid") or raw.get("provider_id")
                
                model = StixLike(
                    indicator = ind_norm or "",
                    indicator_type = type_norm or "",
                    first_seen = first_seen,
                    last_seen = last_seen,
                    confidence = confidence,
                    references = refs,
                    desc = desc,
                    source = source_key,
                    source_event_id = provider_id,
                    raw_sha256 = raw_hash,
                    extra = extra
                )
                
                if not model.indicator:
                    continue
                
                out.write(model.model_dump_json(by_alias=False).encode("utf-8"))
                out.write(b"\n")
                written += 1
    
    return str(out_path), written

def normalize_all_for_date(date_str: str | None = None) -> List[str]:
    cfg = load()
    date_str = date_str or _stamp_date()
    outputs = []
    
    for mp in glob.glob("config/mappings/*.yaml"):
        key = Path(mp).stem
        raw_file = Path(cfg["project"]["raw_dir"]) / key / f"{date_str}.jsonl"
        if raw_file.exists():
            out_path, count = normalize_source(key, date_str)
            print(f"[ok] {key}: normalized {count} -> {out_path}")
            outputs.append(out_path)
    
    return outputs

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        normalize_all_for_date()
    elif len(sys.argv) == 2:
        normalize_all_for_date(sys.argv[1])
    elif len(sys.argv) == 3:
        print(normalize_source(sys.argv[1], sys.argv[2]))
    else:
        raise SystemExit("usage: python -m src.normalizers.normalize_run [YYYY-MM-DD] | [source_key YYYY-MM-DD]")