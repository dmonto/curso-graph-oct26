from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from datetime import date
p=argparse.ArgumentParser()
p.add_argument("--caducidad",required=True,help="AAAA-MM-DD, metadato de la credencial")
a=p.parse_args()
try: days=(date.fromisoformat(a.caducidad)-date.today()).days
except ValueError: p.error("Fecha no válida")
print("Días restantes:",days)
print("CADUCADA" if days<0 else "ROTAR PRONTO" if days<=30 else "VIGENTE según fecha indicada")
print("No se comprueba la credencial ni se muestra su valor.")
raise SystemExit(1 if days<=30 else 0)
