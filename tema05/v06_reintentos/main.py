import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from types import SimpleNamespace
from unittest.mock import Mock, patch
from src.utils.graph_client import ClienteGraph, ErrorGraph
from src.runtime import mostrar, ejecutar

def respuesta(status, retry=None):
    r = Mock()
    r.status_code = status
    r.headers = {} if retry is None else {"Retry-After": str(retry)}
    r.json.return_value = {"value":[]} if status == 200 else {"error":{"code":"TooManyRequests" if status == 429 else "ServiceUnavailable"}}
    return r

def main():
    p = argparse.ArgumentParser(description="Demostración sin red de 429/503 y presupuesto de espera")
    p.add_argument("--escenario", choices=["429", "503", "aplazado"], default="429")
    a = p.parse_args()
    config = SimpleNamespace(graph_api_url="https://graph.microsoft.com/v1.0", timeout_seconds=15)
    with ClienteGraph(config, lambda:"TOKEN_FICTICIO_NO_VALIDO") as g:
        g.sesion.request = Mock(side_effect=[respuesta(503 if a.escenario=="503" else 429, 120 if a.escenario=="aplazado" else 1), respuesta(200)])
        # Se sustituye únicamente la espera para que la demostración sea instantánea.
        with patch("src.utils.graph_client.time.sleep") as dormir:
            try:
                mostrar(g.peticion("GET", "/users"))
            except ErrorGraph as e:
                mostrar(e.como_dict())
                if a.escenario != "aplazado" or e.codigo != "reintento_aplazado":
                    raise
            mostrar({"simulacion":True, "intentos":len(g.historial), "esperas_solicitadas":[x.args[0] for x in dormir.call_args_list], "historial":g.historial})

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
