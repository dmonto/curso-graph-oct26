import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

def required(name):
    value = os.getenv(name, "").strip()
    if not value or "{" in value or "}" in value:
        raise ValueError(f"Completa {name} en {ROOT / '.env'}")
    return value
