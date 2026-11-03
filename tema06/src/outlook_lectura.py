import argparse
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import requests

from src.auditar_directorio import detener_si_fallo_identidad, escribir_csv, uuid_real
from src.utils.auth_msal import crear_cliente, obtener_token
from src.utils.config import leer_config
from src.utils.outlook_client import PREFER, ClienteOutlook

ROOT = Path(__file__).resolve().parents[1]
CAMPOS_MENSAJE = "id,subject,from,receivedDateTime,isRead,hasAttachments,webLink,internetMessageId"
CAMPOS_EVENTO = "id,subject,start,end,type,seriesMasterId,isCancelled,isOrganizer,webLink"
CAMPOS_PROPUESTA = ["clave", "origen", "origen_id", "caso", "titulo", "estado", "responsable_user_id", "web_link"]


def fecha_con_offset(valor):
    fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if fecha.tzinfo is None or fecha.utcoffset() is None:
        raise ValueError("La fecha necesita un offset o Z.")
    return fecha.astimezone(timezone.utc)


def rango(desde, hasta):
    inicio, fin = fecha_con_offset(desde), fecha_con_offset(hasta)
    if not timedelta(0) < fin - inicio <= timedelta(days=31):
        raise ValueError("El rango de prácticas debe ser positivo y de hasta 31 días.")
    return inicio.isoformat().replace("+00:00", "Z"), fin.isoformat().replace("+00:00", "Z")


def segmento(valor):
    if not isinstance(valor, str) or not valor or len(valor) > 4096:
        raise ValueError("Identificador de Outlook no válido.")
    return quote(valor, safe="")


def informe_nuevo(buzon, desde, hasta):
    return {"run_id": str(uuid4()), "fecha_utc": datetime.now(timezone.utc).isoformat(),
            "buzon_id": buzon, "ventana": {"desde": desde, "hasta": hasta},
            "resultado": "error", "error": None, "auth": [], "http": [],
            "colecciones": {}, "propuestas": []}


def recopilar(graph, informe, tamano_pagina=25, max_paginas=100, solo_no_leidos=False):
    buzon = informe["buzon_id"]
    desde, hasta = informe["ventana"]["desde"], informe["ventana"]["hasta"]
    filtro = f"receivedDateTime ge {desde} and receivedDateTime lt {hasta}"
    if solo_no_leidos:
        filtro += " and isRead eq false"
    informe["solo_no_leidos"] = solo_no_leidos
    informe["http"] = graph.historial
    informe["colecciones"]["mensajes"] = graph.listar(
        f"/users/{buzon}/mailFolders/inbox/messages",
        params={"$select": CAMPOS_MENSAJE, "$filter": filtro,
                "$orderby": "receivedDateTime desc", "$top": str(tamano_pagina)},
        headers=PREFER, max_paginas=max_paginas,
    )
    detener_si_fallo_identidad(informe["colecciones"]["mensajes"])
    informe["colecciones"]["eventos"] = graph.listar(
        f"/users/{buzon}/calendarView",
        params={"startDateTime": desde, "endDateTime": hasta,
                "$select": CAMPOS_EVENTO, "$top": str(tamano_pagina)},
        headers=PREFER, max_paginas=max_paginas,
    )
    detener_si_fallo_identidad(informe["colecciones"]["eventos"])
    informe["propuestas"] = construir_propuestas(informe)
    informe["resultado"] = "ok" if all(x["completo"] for x in informe["colecciones"].values()) else "parcial"


def construir_propuestas(informe):
    propuestas = []
    vistas = set()
    for nombre, origen in (("mensajes", "correo"), ("eventos", "evento")):
        coleccion = informe["colecciones"].get(nombre)
        if coleccion is None:
            continue
        for objeto in coleccion["elementos"]:
            asunto = objeto.get("subject") or ""
            coincidencia = re.match(r"^CURSO-((?:FIN|RRHH|MANT)-\d{3}):\s*(.+)$", asunto, re.IGNORECASE)
            if not coincidencia or (origen == "evento" and objeto.get("isCancelled") is True):
                continue
            clave = hashlib.sha256(f"{informe['buzon_id']}|{origen}|{objeto['id']}".encode()).hexdigest()
            if clave in vistas:
                continue
            vistas.add(clave)
            estado = "pendiente_revision" if coleccion["completo"] else "origen_incompleto"
            if origen == "evento" and objeto.get("isCancelled") is not False:
                estado = "evento_no_verificado"
            propuestas.append({"clave": clave, "origen": origen, "origen_id": objeto["id"],
                               "caso": coincidencia[1].upper(), "titulo": coincidencia[2],
                               "estado": estado, "responsable_user_id": "",
                               "web_link": objeto.get("webLink") or ""})
    return propuestas


def correo_resumen(informe, destinatario):
    filas = "".join(f"<li>{escape(x['caso'])}: {escape(x['titulo'])} — {escape(x['estado'])}</li>"
                    for x in informe["propuestas"])
    contenido = (f"<p>Lectura: {escape(informe['resultado'])}.</p>"
                 f"<p>Propuestas recuperadas: {len(informe['propuestas'])}.</p><ul>{filas}</ul>"
                 "<p>Propuestas pendientes de revisión; consultar la auditoría de esta ejecución.</p>")
    return {"message": {"subject": "CURSO-Resumen de buzón y agenda",
                        "body": {"contentType": "HTML", "content": contenido},
                        "toRecipients": [{"emailAddress": {"address": destinatario}}]},
            "saveToSentItems": True}


def propuesta_cita(informe):
    inicio = fecha_con_offset(informe["ventana"]["desde"]) + timedelta(hours=9)
    fin = inicio + timedelta(minutes=30)
    return {"subject": "CURSO-Revisión de automatizaciones", "transactionId": str(uuid4()),
            "start": {"dateTime": inicio.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"},
            "end": {"dateTime": fin.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"},
            "isReminderOn": True, "reminderMinutesBeforeStart": 15}


def guardar_informe(carpeta, informe, destinatario="destinatario@ejemplo.invalid"):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, campos in (("mensajes", ["id", "subject", "receivedDateTime", "isRead", "hasAttachments", "webLink"]),
                           ("eventos", ["id", "subject", "start", "end", "type", "isCancelled", "webLink"])):
        datos = informe["colecciones"].get(nombre)
        if datos is not None:
            escribir_csv(carpeta / f"{nombre}.csv", datos["elementos"], campos)
    escribir_csv(carpeta / "propuestas_tareas.csv", informe["propuestas"], CAMPOS_PROPUESTA)
    if informe["resultado"] != "error":
        for nombre, datos in (("propuesta_correo", correo_resumen(informe, destinatario)),
                               ("propuesta_evento", propuesta_cita(informe))):
            (carpeta / f"{nombre}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    (carpeta / "auditoria.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Lectura de Outlook y propuestas locales.")
    parser.add_argument("--desde", required=True)
    parser.add_argument("--hasta", required=True)
    parser.add_argument("--tamano-pagina", type=int, choices=range(1, 100), default=25)
    parser.add_argument("--max-paginas", type=int, choices=range(1, 1001), default=100)
    parser.add_argument("--solo-no-leidos", action="store_true")
    args = parser.parse_args()
    informe = informe_nuevo(None, args.desde, args.hasta)
    destinatario = "destinatario@ejemplo.invalid"
    salida = 1
    try:
        config = leer_config(validar_identidad=False)
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
        logging.getLogger().setLevel(config.log_level)
        for nombre in ("msal", "urllib3", "requests"):
            logging.getLogger(nombre).setLevel(logging.WARNING)
        desde, hasta = rango(args.desde, args.hasta)
        informe["ventana"] = {"desde": desde, "hasta": hasta}
        informe["buzon_id"] = uuid_real(os.getenv("COURSE_MAILBOX_USER_ID", ""))
        destinatario = os.getenv("COURSE_TEST_RECIPIENT", "").strip() or destinatario
        cliente = crear_cliente(config, "apponly")

        def proveedor():
            return obtener_token(cliente, "apponly", informe["run_id"], informe["auth"], False)

        with ClienteOutlook(config, proveedor) as graph:
            recopilar(graph, informe, args.tamano_pagina, args.max_paginas, args.solo_no_leidos)
        salida = 0 if informe["resultado"] == "ok" else 2
    except KeyboardInterrupt:
        informe["error"] = "ejecucion_cancelada"
        salida = 130
    except requests.RequestException as error:
        informe["error"] = f"red_auth_{type(error).__name__}"
    except (RuntimeError, ValueError) as error:
        informe["error"] = error.como_dict() if hasattr(error, "como_dict") else "configuracion_o_autenticacion_invalida"
    except OSError:
        informe["error"] = "archivo_no_disponible"
    informe["exit_code"] = salida
    carpeta = ROOT / "resultados" / f"tema6_{informe['run_id']}"
    try:
        guardar_informe(carpeta, informe, destinatario)
    except OSError:
        print("No se pudo guardar la auditoría de Outlook.")
        return 1
    print(f"Resultado: {informe['resultado']}; exit_code={salida}; carpeta={carpeta}")
    return salida


if __name__ == "__main__":
    raise SystemExit(main())
