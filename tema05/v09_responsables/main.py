import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse, os
from src.runtime import conectar, mostrar, ejecutar
from src.directorio import uuid_real, leer_casos, preparar_responsables, escribir_csv, CAMPOS_RESPONSABLE

def main():
    p = argparse.ArgumentParser(description="Preparar responsables para Planner y Teams")
    p.add_argument("--entrada", default="datos/casos_tema5.csv")
    p.add_argument("--grupo-id")
    a = p.parse_args()
    casos = leer_casos(ROOT / a.entrada)
    with conectar() as g:
        gid = uuid_real(a.grupo_id or os.getenv("GROUP_ID", ""))
        miembros = g.listar(f"/groups/{gid}/members")
        filas = preparar_responsables(g, casos, gid, miembros)
    carpeta = Path(__file__).resolve().parent / "resultados"
    carpeta.mkdir(exist_ok=True)
    escribir_csv(carpeta/"responsables.csv", filas, CAMPOS_RESPONSABLE)
    mostrar({"responsables":filas, "miembros_completos":miembros["completo"], "archivo":str(carpeta/"responsables.csv")})
    return 0 if miembros["completo"] and all(x["estado"]=="listo" for x in filas) else 2

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
