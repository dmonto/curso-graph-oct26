import argparse
import json
from types import SimpleNamespace

import requests

from src.outlook_lectura import ROOT, guardar_informe, informe_nuevo, recopilar
from src.utils.outlook_client import ClienteOutlook

BUZON = "00000000-0000-4000-8000-000000000011"
BASE = "https://graph.microsoft.com/v1.0"
DESDE = "2026-10-05T22:00:00Z"
HASTA = "2026-10-06T22:00:00Z"


def respuesta(datos):
    valor = requests.Response()
    valor.status_code = 200
    valor._content = json.dumps(datos).encode()
    valor.headers["request-id"] = "00000000-0000-4000-8000-000000000031"
    return valor


def datos_demo():
    mensajes = [{"id": f"MSG-{i}", "subject": asunto, "isRead": False,
                 "hasAttachments": i == 1, "receivedDateTime": "2026-10-06T08:00:00Z",
                 "webLink": "https://outlook.office.com/"} for i, asunto in enumerate([
                     "CURSO-FIN-001: Revisar petición de proveedor",
                     "CURSO-RRHH-001: Revisar consulta laboral",
                     "CURSO-MANT-001: Revisar incidencia de centro",
                     "Boletín informativo sin propuesta de tarea",
                 ], 1)]
    eventos = [{"id": f"EVT-{i}", "subject": asunto, "isCancelled": i == 3,
                "isOrganizer": True, "type": "occurrence" if i == 1 else "singleInstance",
                "start": {"dateTime": "2026-10-06T09:00:00", "timeZone": "UTC"},
                "end": {"dateTime": "2026-10-06T09:30:00", "timeZone": "UTC"}}
               for i, asunto in enumerate([
                   "CURSO-MANT-002: Visita de mantenimiento",
                   "CURSO-FIN-001: Revisión financiera",
                   "CURSO-RRHH-001: Reunión cancelada",
               ], 1)]
    return mensajes, eventos


class SesionDemo:
    def __init__(self):
        mensajes, eventos = datos_demo()
        self.paginas = {
            BASE + f"/users/{BUZON}/mailFolders/inbox/messages": {"value": mensajes[:2], "@odata.nextLink": BASE + "/demo/mensajes2"},
            BASE + "/demo/mensajes2": {"value": mensajes[2:]},
            BASE + f"/users/{BUZON}/calendarView": {"value": eventos[:2], "@odata.nextLink": BASE + "/demo/eventos2"},
            BASE + "/demo/eventos2": {"value": eventos[2:]},
        }

    def request(self, metodo, url, **kwargs):
        if metodo != "GET" or url not in self.paginas:
            raise RuntimeError("Consulta no prevista en el laboratorio local.")
        return respuesta(self.paginas[url])

    def close(self):
        pass


def main():
    parser = argparse.ArgumentParser(description="Lectura de Outlook con datos ficticios, sin red.")
    parser.add_argument("--max-paginas", type=int, choices=range(1, 101), default=100)
    args = parser.parse_args()
    informe = informe_nuevo(BUZON, DESDE, HASTA)
    informe["modo"] = "simulacion_local"
    with ClienteOutlook(SimpleNamespace(graph_api_url=BASE, timeout_seconds=15),
                        lambda: "TOKEN_FICTICIO_SIN_VALIDEZ") as graph:
        graph.sesion.close()
        graph.sesion = SesionDemo()
        recopilar(graph, informe, tamano_pagina=2, max_paginas=args.max_paginas)
    salida = 0 if informe["resultado"] == "ok" else 2
    informe["exit_code"] = salida
    carpeta = ROOT / "resultados" / f"tema6_demo_{informe['run_id']}"
    guardar_informe(carpeta, informe)
    print(f"Demo: {informe['resultado']}; propuestas={len(informe['propuestas'])}; carpeta={carpeta}")
    return salida


if __name__ == "__main__":
    raise SystemExit(main())
