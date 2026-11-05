from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Convertir el contrato Graph en un payload para un flujo."""
import json
from src.plantillas_teams import mensaje_resumen, mensaje_tarjeta, validar_mensaje
from src.ejemplos import guardar, ENLACE_DEMO

def main():
    fuente = json.loads((BASE / "datos/estado_tema7_demo.json").read_text(encoding="utf-8"))
    _, resumen = mensaje_resumen(fuente["propuestas"], fuente["resultado_lectura"] == "ok", ENLACE_DEMO)
    graph_payload = mensaje_tarjeta(resumen, ENLACE_DEMO)
    validar_mensaje(graph_payload)
    tarjeta = json.loads(graph_payload["attachments"][0]["content"])
    payload_flujo = {
        "type": "message",
        "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive",
                         "contentUrl": None, "content": tarjeta}],
    }
    guardar(BASE / "resultados/tarjeta_teams.json", graph_payload)
    guardar(BASE / "resultados/payload_flujo_tema7.json", payload_flujo)
    print("Graph: content es cadena JSON. Flujo: content es objeto. No se envía ninguna petición.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
