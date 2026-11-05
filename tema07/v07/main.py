from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Consultar filesFolder y extraer la referencia de SharePoint."""
from src.ejemplos import ejecutar_teams, guardar

def main():
    args = sys.argv[1:] or ["--local", "carpeta"]
    codigo, informe = ejecutar_teams(BASE, args)
    if codigo != 0:
        return codigo
    ubicacion = informe["datos"]
    referencia = {
        "driveId": ubicacion["parentReference"]["driveId"],
        "itemId": ubicacion["id"],
        "webUrl": ubicacion["webUrl"],
    }
    guardar(BASE / "resultados/referencia_carpeta.json", referencia)
    print(referencia)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
