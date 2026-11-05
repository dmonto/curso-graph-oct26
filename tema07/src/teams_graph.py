import argparse
import csv
import json
import logging
import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote
from uuid import uuid4

import requests

from src.auditar_directorio import uuid_real
from src.plantillas_teams import validar_mensaje
from src.utils.config import leer_config
from src.utils.teams_client import ClienteTeams, cliente_autenticado

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://graph.microsoft.com/v1.0"
EQUIPO_DEMO = "00000000-0000-4000-8000-000000000071"
CANAL_DEMO = "19:CURSO-DEMO@thread.tacv2"
PERMISOS = {
    "canales": ["Channel.ReadBasic.All"], "miembros": ["TeamMember.Read.All"],
    "hilos": ["ChannelMessage.Read.All"], "carpeta": ["Files.Read.All"],
    "crear-canal": ["Channel.Create"],
    "publicar": ["Channel.ReadBasic.All", "ChannelMessage.Send"],
    "responder": ["Channel.ReadBasic.All", "ChannelMessage.Send"],
}


def segmento(valor):
    if not isinstance(valor, str) or not valor or len(valor) > 4096:
        raise ValueError("Se necesita un identificador opaco válido.")
    return quote(valor, safe="")


class TextoHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fragmentos = []

    def handle_data(self, data):
        self.fragmentos.append(data)


def texto_visible(mensaje):
    cuerpo = mensaje.get("body") or {}
    texto = cuerpo.get("content") or ""
    if cuerpo.get("contentType") == "html":
        parser = TextoHTML()
        parser.feed(texto)
        return " ".join(parser.fragmentos)
    return texto


def fallo_identidad(coleccion):
    error = coleccion.get("error")
    return bool(error and (error.get("http_status") == 401 or error.get("codigo") == "autenticacion_fallida"))


def leer_hilos(graph, ruta, max_paginas):
    raices = graph.listar(ruta + "/messages", params={"$top": "2"}, max_paginas=max_paginas)
    resultado = {"raices": raices, "respuestas": {}, "elementos": [], "completo": False}
    for mensaje in raices["elementos"]:
        resultado["elementos"].append({**mensaje, "raiz_id": mensaje["id"], "origen": "raiz"})
    if fallo_identidad(raices):
        return resultado
    for mensaje in raices["elementos"]:
        if mensaje.get("deletedDateTime"):
            continue
        respuestas = graph.listar(ruta + f"/messages/{segmento(mensaje['id'])}/replies",
                                  params={"$top": "2"}, max_paginas=max_paginas)
        resultado["respuestas"][mensaje["id"]] = respuestas
        resultado["elementos"].extend({**x, "raiz_id": mensaje["id"], "origen": "respuesta"}
                                       for x in respuestas["elementos"])
        if fallo_identidad(respuestas):
            return resultado
    resultado["completo"] = raices["completo"] and all(x["completo"] for x in resultado["respuestas"].values())
    return resultado


def buscar_observados(mensajes, termino):
    return [x for x in mensajes if not x.get("deletedDateTime")
            and termino.casefold() in texto_visible(x).casefold()]


def ejecutar(graph, args, equipo, canal):
    raiz = f"/teams/{equipo}"
    ruta = raiz + "/channels/" + segmento(canal) if canal else None
    if args.operacion == "canales":
        return graph.listar(raiz + "/channels", params={"$select": "id,displayName,membershipType,isArchived"},
                            max_paginas=args.max_paginas)
    if args.operacion == "miembros":
        return graph.listar(raiz + "/members", params={"$select": "id,userId,displayName,roles,tenantId"},
                            max_paginas=args.max_paginas)
    if args.operacion == "hilos":
        datos = leer_hilos(graph, ruta, args.max_paginas)
        datos["coincidencias"] = buscar_observados(datos["elementos"], args.termino)
        datos["termino_local"] = args.termino
        return datos
    if args.operacion == "carpeta":
        return graph.peticion("GET", ruta + "/filesFolder")
    if args.operacion == "crear-canal":
        nombre = args.nombre or ""
        if not nombre.startswith("CURSO-") or len(nombre) > 50:
            raise ValueError("Usa un nombre CURSO- de hasta 50 caracteres.")
        payload = {"displayName": nombre, "description": "Prácticas de Microsoft Graph", "membershipType": "standard"}
        destino = raiz + "/channels"
    else:
        archivo = ROOT / args.archivo
        if archivo.stat().st_size > 32 * 1024:
            raise ValueError("El archivo de propuesta supera el límite local.")
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        validar_mensaje(payload)
        destino = ruta + "/messages"
        if args.operacion == "responder":
            destino += f"/{segmento(args.mensaje_id)}/replies"
        if args.aplicar:
            contexto = graph.peticion("GET", ruta, params={"$select": "id,displayName,membershipType,isArchived"})
            if (not (contexto.get("displayName") or "").startswith("CURSO-")
                    or contexto.get("membershipType") != "standard" or contexto.get("isArchived") is not False):
                raise RuntimeError("Publica en un canal CURSO- estándar y activo de prácticas.")
    objeto = graph.escribir("POST", destino, cuerpo=payload, esperado=201) if args.aplicar else None
    return {"estado": "creado_201" if args.aplicar else "simulado", "ruta": destino,
            "payload": payload, "objeto_creado": objeto}


class SesionDemo:
    def __init__(self):
        raiz = BASE + f"/teams/{EQUIPO_DEMO}"
        canal = raiz + "/channels/" + segmento(CANAL_DEMO)
        canales = [{"id": CANAL_DEMO, "displayName": "CURSO-Automatizaciones", "membershipType": "standard", "isArchived": False},
                   {"id": "19:RRHH-DEMO@thread.tacv2", "displayName": "RRHH", "membershipType": "private"}]
        miembros = [{"id": "MEMBERSHIP/LAURA=", "userId": "00000000-0000-4000-8000-000000000011",
                     "displayName": "Laura Demo", "roles": ["owner"]},
                    {"id": "MEMBERSHIP/RAFA=", "userId": "00000000-0000-4000-8000-000000000012",
                     "displayName": "Rafa Demo", "roles": []}]
        def mensaje(identificador, texto):
            return {"id": identificador, "body": {"contentType": "html", "content": texto},
                    "deletedDateTime": None, "webUrl": "https://teams.microsoft.com/"}
        mensajes = [mensaje("1001", "<p>CURSO-FIN-001: Revisar petición de proveedor</p>"),
                    mensaje("1002", "<p>Boletín sin solicitud de trabajo</p>"),
                    mensaje("1003", "<p>CURSO-MANT-001: Revisar visita al centro</p>")]
        self.paginas = {
            raiz + "/channels": {"value": canales}, raiz + "/members": {"value": miembros},
            canal: canales[0], canal + "/messages": {"value": mensajes[:2], "@odata.nextLink": BASE + "/curso-demo/pagina2"},
            BASE + "/curso-demo/pagina2": {"value": mensajes[2:]},
            canal + "/messages/1001/replies": {"value": [mensaje("2001", "<p>CURSO-FIN-001: Revisión confirmada</p>")]},
            canal + "/messages/1002/replies": {"value": []}, canal + "/messages/1003/replies": {"value": []},
            canal + "/filesFolder": {"id": "CARPETA-DEMO", "parentReference": {"driveId": "DRIVE-DEMO"},
                "webUrl": "https://contoso.sharepoint.com/sites/Curso/Shared%20Documents/CURSO-Automatizaciones"},
        }

    def request(self, metodo, url, **kwargs):
        if metodo != "GET" or url not in self.paginas:
            raise RuntimeError("Operación no prevista en la simulación local.")
        respuesta = requests.Response()
        respuesta.status_code = 200
        respuesta._content = json.dumps(self.paginas[url]).encode("utf-8")
        respuesta.headers["request-id"] = str(uuid4())
        return respuesta

    def close(self):
        pass


def main():
    parser = argparse.ArgumentParser(description="Teams con Graph: lecturas y propuestas revisables.")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--sin-interaccion", action="store_true")
    parser.add_argument("--apponly", action="store_true",
                        help="Autentica con la cuenta de aplicación (client credentials).")
    parser.add_argument("--max-paginas", type=int, choices=range(1, 11), default=3)
    parser.add_argument("operacion", choices=tuple(PERMISOS))
    parser.add_argument("--archivo")
    parser.add_argument("--nombre")
    parser.add_argument("--mensaje-id")
    parser.add_argument("--termino", default="CURSO-")
    args = parser.parse_args()
    informe = {"run_id": str(uuid4()), "fecha_utc": datetime.now(timezone.utc).isoformat(),
               "modo": "simulacion_local" if args.local else ("apponly" if args.apponly else "delegada"), "operacion": args.operacion,
               "aplicar": args.aplicar, "equipo_id": None, "canal_id": None,
               "auth": [], "http": [], "datos": None, "error": None}
    salida = 1
    try:
        if args.local and args.apponly:
            raise ValueError("--apponly requiere ejecución real; no se combina con --local.")
        if args.apponly and args.operacion in {"crear-canal", "publicar", "responder"} and args.aplicar:
            raise ValueError("Graph no permite crear canales ni publicar mensajes solo con permisos de aplicación.")
        if args.local and args.aplicar:
            raise ValueError("La simulación local conserva propuestas y no aplica escrituras.")
        config = SimpleNamespace(graph_api_url=BASE, timeout_seconds=15) if args.local else leer_config(validar_identidad=False)
        equipo = EQUIPO_DEMO if args.local else uuid_real(os.getenv("TEAM_ID", ""))
        canal = CANAL_DEMO if args.local else os.getenv("CHANNEL_ID", "").strip()
        informe["equipo_id"], informe["canal_id"] = equipo, canal
        necesita_graph = args.operacion in {"canales", "miembros", "hilos", "carpeta"} or args.aplicar
        if necesita_graph:
            if args.local:
                graph = ClienteTeams(config, lambda: "TOKEN_FICTICIO_SIN_VALIDEZ")
                graph.sesion.close()
                graph.sesion = SesionDemo()
            else:
                logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
                for nombre in ("msal", "urllib3", "requests"):
                    logging.getLogger(nombre).setLevel(logging.WARNING)
                scopes = ["https://graph.microsoft.com/" + x for x in PERMISOS[args.operacion]]
                graph = cliente_autenticado(config, scopes, informe, not args.sin_interaccion, args.apponly)
            with graph:
                informe["http"] = graph.historial
                informe["datos"] = ejecutar(graph, args, equipo, canal)
        else:
            informe["datos"] = ejecutar(None, args, equipo, canal)
        salida = 2 if informe["datos"].get("completo") is False else 0
    except KeyboardInterrupt:
        informe["error"] = "ejecucion_cancelada"
        salida = 130
    except requests.RequestException as error:
        informe["error"] = f"red_auth_{type(error).__name__}"
    except (RuntimeError, ValueError, TypeError, AttributeError, KeyError) as error:
        informe["error"] = error.como_dict() if hasattr(error, "como_dict") else "entrada_o_autorizacion_invalida"
    except OSError:
        informe["error"] = "archivo_no_disponible"
    informe["exit_code"] = salida
    carpeta = ROOT / "resultados" / f"tema7_{informe['run_id']}"
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "auditoria.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.operacion == "hilos" and informe["datos"] is not None:
            with (carpeta / "hilos.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=["id", "raiz_id", "origen", "texto"], delimiter=";")
                escritor.writeheader()
                for mensaje in informe["datos"]["elementos"]:
                    escritor.writerow({"id": mensaje["id"], "raiz_id": mensaje["raiz_id"],
                                       "origen": mensaje["origen"], "texto": texto_visible(mensaje)})
    except OSError:
        print("No se pudo guardar la auditoría de Teams.")
        return 1
    print(f"Operación: {args.operacion}; exit_code={salida}; carpeta={carpeta}")
    return salida


if __name__ == "__main__":
    raise SystemExit(main())
