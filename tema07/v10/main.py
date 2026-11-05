from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Escoger HTML y tarjeta según el alcance y los pendientes."""
import json
from src.plantillas_teams import mensaje_resumen, mensaje_tarjeta, validar_mensaje
from src.ejemplos import guardar, ENLACE_DEMO

def main():
    fuente = json.loads((BASE / "datos/estado_tema7_demo.json").read_text(encoding="utf-8"))
    for estado, completa in [("completa_con_pendientes", True), ("parcial", False)]:
        filas = fuente["propuestas"] if completa else fuente["propuestas"][:4]
        html, resumen = mensaje_resumen(filas, completa, ENLACE_DEMO)
        tarjeta = mensaje_tarjeta(resumen, ENLACE_DEMO)
        validar_mensaje(html)
        validar_mensaje(tarjeta)
        guardar(BASE / f"resultados/{estado}/mensaje_teams.json", html)
        guardar(BASE / f"resultados/{estado}/tarjeta_teams.json", tarjeta)
        guardar(BASE / f"resultados/{estado}/contadores.json", resumen)
    print("Completa: 5/3/2. Parcial: 4/0/4. Los contadores se refieren a propuestas observadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
