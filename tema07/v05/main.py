from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Comparar lectura completa y parcial de raíces y respuestas."""
from src.ejemplos import ejecutar_teams, guardar

def main():
    if sys.argv[1:]:
        return ejecutar_teams(BASE, sys.argv[1:])[0]
    comparacion = []
    for limite in (3, 1):
        codigo, informe = ejecutar_teams(BASE, ["--local", "--max-paginas", str(limite), "hilos", "--termino", "CURSO-"])
        if codigo not in (0, 2) or informe is None or informe["datos"] is None:
            return 1
        datos = informe["datos"]
        comparacion.append({
            "max_paginas": limite, "exit_code_lectura": codigo, "completo": datos["completo"],
            "raices": len(datos["raices"]["elementos"]),
            "respuestas": sum(len(x["elementos"]) for x in datos["respuestas"].values()),
            "coincidencias": len(datos["coincidencias"]),
            "run_id": informe["run_id"],
        })
    guardar(BASE / "resultados/comparacion.json", comparacion)
    print(comparacion)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
