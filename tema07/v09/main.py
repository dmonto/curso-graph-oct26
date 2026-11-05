from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Leer una auditoría parcial y conservar las referencias de cada intento."""
from src.ejemplos import ejecutar_teams, guardar

def main():
    codigo, auditoria = ejecutar_teams(BASE, ["--local", "--max-paginas", "1", "hilos"])
    if codigo != 2:
        return 1
    datos = auditoria["datos"]
    diagnostico = {
        "run_id": auditoria["run_id"], "exit_code": codigo,
        "lectura_completa": datos["completo"],
        "error_raices": datos["raices"]["error"],
        "observados": len(datos["elementos"]),
        "coincidencias": len(datos["coincidencias"]),
        "intentos": auditoria["http"],
        "accion": "Conservar lo observado y completar las páginas pendientes antes de afirmar cobertura completa.",
    }
    guardar(BASE / "resultados/diagnostico.json", diagnostico)
    print(diagnostico["accion"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
