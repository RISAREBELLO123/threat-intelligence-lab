from src.utils.env import load
from src.collectors.rest_generic import collect

def run_all():
    """
    Iterate over all enabled sources and invoke the collector.
    """
    cfg = load()
    for s in cfg.get("sources", []):
        if not s.get("enabled"):
            continue
        
        if s.get("type") == "generic_rest":
            try:
                path = collect(s)
                print(f"✓ {s.get('key')} -> {path}")
            except Exception as e:
                print(f"✗ {s.get('key')} failed: {e}")
        else:
            print(f"⊘ {s.get('key')} (type '{s.get('type')}' not implemented yet)")

if __name__ == "__main__":
    run_all()