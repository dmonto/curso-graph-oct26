import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import requests

def segment(value):
    return quote(value, safe="")

def utc_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def show(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def output(script, name, content):
    folder = Path(script).resolve().parent / "salidas"
    folder.mkdir(exist_ok=True)
    path = folder / name
    path.write_text(content, encoding="utf-8")
    print(f"Guardado: {path}")
    return path

def run(main):
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-code", action="store_true")
    args = parser.parse_args()
    try:
        main(args)
    except (ValueError, RuntimeError, requests.RequestException) as exc:
        parser.exit(1, f"Error: {exc}\n")
