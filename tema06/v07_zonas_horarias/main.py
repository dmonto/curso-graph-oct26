from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

p = argparse.ArgumentParser()
p.add_argument("--dia", default="2026-10-06")
p.add_argument("--zona", default="Europe/Madrid")
a = p.parse_args()
dia = date.fromisoformat(a.dia)
zona = ZoneInfo(a.zona)
inicio = datetime.combine(dia, time.min, zona)
fin = datetime.combine(dia + timedelta(days=1), time.min, zona)
for nombre, fecha in [("desde", inicio), ("hasta", fin)]:
    print(nombre, "local:", fecha.isoformat(), "UTC:", fecha.astimezone(timezone.utc).isoformat())
print("Horas reales:", (fin.astimezone(timezone.utc) - inicio.astimezone(timezone.utc)).total_seconds()/3600)
