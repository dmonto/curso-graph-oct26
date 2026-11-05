from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Preparar una mención y simular su publicación."""
from src.plantillas_teams import mensaje_con_mencion, validar_mensaje
from src.ejemplos import guardar, ejecutar_teams

def main():
    payload = mensaje_con_mencion("00000000-0000-4000-8000-000000000011", "Laura Demo")
    validar_mensaje(payload)
    guardar(BASE / "resultados/mencion_tema7.json", payload)
    return ejecutar_teams(BASE, ["--local", "publicar", "--archivo", "resultados/mencion_tema7.json"])[0]


if __name__ == "__main__":
    raise SystemExit(main())
