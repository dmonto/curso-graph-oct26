"""Ayudas de ejecución: cada ejemplo conserva entradas y salidas en su carpeta."""
import json
import sys
from pathlib import Path
from src import teams_graph

ENLACE_DEMO = "https://contoso.sharepoint.com/sites/Curso/Shared%20Documents/informe_tema6.html"

def guardar(ruta, datos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

def ejecutar_teams(base, argumentos):
    anterior_root, anterior_argv = teams_graph.ROOT, sys.argv
    teams_graph.ROOT = Path(base)
    sys.argv = ["teams_graph", *argumentos]
    antes = set((Path(base) / "resultados").glob("tema7_*/auditoria.json"))
    try:
        codigo = teams_graph.main()
    finally:
        teams_graph.ROOT, sys.argv = anterior_root, anterior_argv
    nuevas = set((Path(base) / "resultados").glob("tema7_*/auditoria.json")) - antes
    informe = json.loads(next(iter(nuevas)).read_text(encoding="utf-8")) if len(nuevas) == 1 else None
    return codigo, informe
