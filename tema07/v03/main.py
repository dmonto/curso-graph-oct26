from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Construir HTML y Adaptive Card con los mismos contadores."""
import json
from src.plantillas_teams import mensaje_resumen, mensaje_tarjeta, validar_mensaje
from src.ejemplos import guardar, ENLACE_DEMO

def main():
    fuente = json.loads((BASE / "datos/estado_tema7_demo.json").read_text(encoding="utf-8"))
    html, resumen = mensaje_resumen(fuente["propuestas"], fuente["resultado_lectura"] == "ok", ENLACE_DEMO)
    tarjeta = mensaje_tarjeta(resumen, ENLACE_DEMO)
    for nombre, mensaje in [("mensaje_teams", html), ("tarjeta_teams", tarjeta)]:
        validar_mensaje(mensaje)
        guardar(BASE / f"resultados/{nombre}.json", mensaje)
    guardar(BASE / "resultados/contadores.json", resumen)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
