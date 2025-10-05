from pathlib import Path
from dotenv import load_dotenv
import os
import yaml

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
CFG_PATH = ROOT / "config" / "config.yaml"

def load():
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg

def getenv(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)