from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
from pathlib import Path
with (Path(__file__).parent/"permisos.csv").open(encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f): print(row)
