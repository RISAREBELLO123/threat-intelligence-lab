from src.utils.env import load
from src.utils import http

print("Testing Module 1 setup...")

try:
    cfg = load()
    print("✓ Config loaded successfully")
    print(f"  Project name: {cfg['project']['name']}")
    print(f"  Sources configured: {len(cfg.get('sources', []))}")
except Exception as e:
    print(f"✗ Config failed: {e}")
    exit(1)

try:
    resp = http.get("https://jsonplaceholder.typicode.com/posts/1")
    print(f"✓ HTTP test successful: {resp.status_code}")
except Exception as e:
    print(f"✗ HTTP test failed: {e}")
    exit(1)

print("\n✓✓✓ Module 1 Complete! ✓✓✓")