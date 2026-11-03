import argparse
import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import requests

from src.auditar_directorio import uuid_real
from src.outlook_lectura import fecha_con_offset, segmento
from src.utils.auth_msal import crear_cliente, obtener_token
from src.utils.config import leer_config
from src.utils.outlook_client import PREFER, ClienteOutlook

ROOT = Path(__file__).resolve().parents[1]


def leer_json(ruta):
    if ruta.stat().st_size > 256 * 1024:
        raise ValueError("El JSON de prácticas supera el límite local.")
    dato = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(dato, dict):
        raise ValueError("Se necesita un objeto JSON.")
    return dato


def adjunto_pequeno(ruta):
    if ruta.stat().st_size > 128 * 1024:
        raise ValueError("El adjunto de prácticas debe tener como máximo 128 KiB.")
    datos = ruta.read_bytes()
    return {"@odata.type": "#microsoft.graph.fileAttachment", "name": ruta.name,
            "contentBytes": base64.b64encode(datos).decode("ascii")}


def validar_correo(payload, destinatario):
    if not destinatario or "@" not in destinatario or destinatario.endswith(".invalid"):
        raise RuntimeError("Configura un destinatario real del laboratorio.")
    if set(payload) - {"message", "saveToSentItems"} or payload.get("saveToSentItems") is not True:
        raise ValueError("Utiliza el formato de correo del laboratorio.")
    mensaje = payload.get("message", {})
    if set(mensaje) - {"subject", "body", "toRecipients", "attachments"}:
        raise ValueError("El correo de prácticas admite asunto, cuerpo y un destinatario.")
    if not (mensaje.get("subject") or "").startswith("CURSO-"):
        raise ValueError("El asunto debe empezar por CURSO-.")
    cuerpo = mensaje.get("body", {})
    if cuerpo.get("contentType") not in {"Text", "HTML"} or not isinstance(cuerpo.get("content"), str):
        raise ValueError("Indica un cuerpo Text o HTML.")
    receptores = mensaje.get("toRecipients", [])
    if len(receptores) != 1:
        raise ValueError("Se admite un destinatario de prácticas.")
    direccion = receptores[0].get("emailAddress", {}).get("address", "")
    if direccion.strip().casefold() != destinatario.strip().casefold():
        raise ValueError("El destinatario no coincide con COURSE_TEST_RECIPIENT.")
    adjuntos = mensaje.get("attachments", [])
    if not isinstance(adjuntos, list) or len(adjuntos) > 1:
        raise ValueError("Se admite un adjunto pequeño de prácticas.")
    for adjunto in adjuntos:
        texto = adjunto.get("contentBytes", "")
        if adjunto.get("@odata.type") != "#microsoft.graph.fileAttachment" or len(texto) > 180000:
            raise ValueError("Utiliza un fileAttachment pequeño.")
        datos = base64.b64decode(texto, validate=True)
        if len(datos) > 128 * 1024:
            raise ValueError("El adjunto supera el límite local.")


def validar_cita(payload, crear=False):
    admitidos = {"subject", "start", "end", "isReminderOn", "reminderMinutesBeforeStart"}
    if crear:
        admitidos.add("transactionId")
    if set(payload) - admitidos or not (payload.get("subject") or "").startswith("CURSO-"):
        raise ValueError("Utiliza únicamente los campos de la cita de prácticas.")
    if crear:
        uuid_real(payload.get("transactionId"))
    fechas = []
    for campo in ("start", "end"):
        dato = payload.get(campo, {})
        if dato.get("timeZone") != "UTC":
            raise ValueError("El ejemplo de escritura utiliza fechas UTC.")
        texto = dato.get("dateTime", "")
        if not isinstance(texto, str):
            raise ValueError("Fecha no válida.")
        fecha = fecha_con_offset(texto + "Z")
        fechas.append(fecha)
    if fechas[1] <= fechas[0]:
        raise ValueError("El fin debe ser posterior al inicio.")


def ejecutar(graph, buzon, args, carpeta, destinatario):
    raiz = f"/users/{buzon}"
    if args.operacion == "mensaje":
        return graph.peticion("GET", f"{raiz}/messages/{segmento(args.mensaje_id)}", params={
            "$select": "id,subject,from,body,bodyPreview,hasAttachments,webLink"
        }, headers={"Prefer": PREFER["Prefer"] + ', outlook.body-content-type="text"'})
    if args.operacion == "adjuntos":
        ruta = f"{raiz}/messages/{segmento(args.mensaje_id)}/attachments"
        listado = graph.listar(ruta, params={"$select": "id,name,size,contentType,isInline"}, headers=PREFER)
        listado["descargas"] = []
        error_lectura = listado.get("error")
        if error_lectura and (error_lectura.get("http_status") == 401
                              or error_lectura.get("codigo") == "autenticacion_fallida"):
            listado["descarga_interrumpida"] = "autenticacion_fallida"
            return listado
        if args.descargar:
            for adjunto in listado["elementos"]:
                fila = {"id": adjunto["id"], "nombre_original": adjunto.get("name"), "estado": "requiere_revision"}
                listado["descargas"].append(fila)
                if adjunto.get("@odata.type") != "#microsoft.graph.fileAttachment" or adjunto.get("isInline") is not False:
                    continue
                if not isinstance(adjunto.get("size"), int) or adjunto["size"] > 2 * 1024 * 1024:
                    fila["estado"] = "limite_o_tamano_desconocido"
                    continue
                try:
                    detalle = graph.descargar(ruta + f"/{segmento(adjunto['id'])}/$value", carpeta / f"adjunto_{uuid4()}.bin")
                    fila.update(detalle)
                    fila["estado"] = "descargado"
                except RuntimeError as error:
                    fila["estado"] = "error_descarga"
                    fila["error"] = error.como_dict() if hasattr(error, "como_dict") else "fallo_descarga"
                    if isinstance(fila["error"], dict) and (fila["error"].get("http_status") == 401
                            or fila["error"].get("codigo") == "autenticacion_fallida"):
                        listado["descarga_interrumpida"] = "autenticacion_fallida"
                        break
                except OSError:
                    fila["estado"] = "error_descarga"
                    fila["error"] = "archivo_no_disponible"
        return listado
    if args.operacion == "enviar-correo":
        payload = leer_json(ROOT / args.archivo)
        validar_correo(payload, destinatario)
        if args.aplicar:
            graph.escribir("POST", raiz + "/sendMail", cuerpo=payload, esperados=(202,))
        return {"estado": "aceptado_202" if args.aplicar else "simulado", "operacion": args.operacion}
    if args.operacion == "crear-cita":
        payload = leer_json(ROOT / args.archivo)
        validar_cita(payload, crear=True)
        dato = graph.escribir("POST", raiz + "/events", cuerpo=payload, esperados=(201,)) if args.aplicar else None
        return {"estado": "creado_201" if args.aplicar else "simulado", "evento": dato,
                "transaction_id": payload["transactionId"]}
    ruta = raiz + "/events/" + segmento(args.evento_id)
    evento = graph.peticion("GET", ruta, params={"$select": "id,subject,isOrganizer,attendees,isCancelled,type"}, headers=PREFER)
    if not (evento.get("subject") or "").startswith("CURSO-") or evento.get("isOrganizer") is not True:
        raise RuntimeError("Utiliza un evento CURSO- organizado por el buzón de prácticas.")
    asistentes = evento.get("attendees")
    if not isinstance(asistentes, list):
        raise RuntimeError("No se pudo verificar la lista de asistentes.")
    if args.operacion in {"actualizar-cita", "eliminar-cita"}:
        if asistentes or evento.get("type") != "singleInstance":
            raise RuntimeError("Esta operación de prácticas requiere una cita simple sin asistentes.")
        if args.operacion == "actualizar-cita":
            payload = leer_json(ROOT / args.archivo)
            validar_cita(payload)
            dato = graph.escribir("PATCH", ruta, cuerpo=payload, esperados=(200,)) if args.aplicar else None
            return {"estado": "actualizado_200" if args.aplicar else "simulado", "evento": dato}
        if args.aplicar:
            graph.escribir("DELETE", ruta, esperados=(204,))
        return {"estado": "eliminado_204" if args.aplicar else "simulado"}
    if not asistentes or not destinatario or any(
        x.get("emailAddress", {}).get("address", "").casefold() != destinatario.casefold() for x in asistentes
    ):
        raise RuntimeError("La cancelación requiere una reunión con asistentes autorizados del laboratorio.")
    if args.aplicar:
        graph.escribir("POST", ruta + "/cancel", cuerpo={"comment": "Cancelación de prácticas CURSO-."}, esperados=(202,))
    return {"estado": "cancelacion_aceptada_202" if args.aplicar else "simulado"}


def main():
    parser = argparse.ArgumentParser(description="Operaciones de Outlook; escrituras simuladas por defecto.")
    parser.add_argument("--aplicar", action="store_true")
    operaciones = parser.add_subparsers(dest="operacion", required=True)
    mensaje = operaciones.add_parser("mensaje")
    mensaje.add_argument("--mensaje-id", required=True)
    adjuntos = operaciones.add_parser("adjuntos")
    adjuntos.add_argument("--mensaje-id", required=True)
    adjuntos.add_argument("--descargar", action="store_true")
    for nombre in ("enviar-correo", "crear-cita", "actualizar-cita"):
        modo = operaciones.add_parser(nombre)
        modo.add_argument("--archivo", required=True)
        if nombre == "actualizar-cita":
            modo.add_argument("--evento-id", required=True)
    for nombre in ("eliminar-cita", "cancelar-reunion"):
        modo = operaciones.add_parser(nombre)
        modo.add_argument("--evento-id", required=True)
    args = parser.parse_args()
    informe = {"run_id": str(uuid4()), "fecha_utc": datetime.now(timezone.utc).isoformat(),
               "operacion": args.operacion, "aplicar": args.aplicar, "buzon_id": None,
               "auth": [], "http": [], "resultado": None, "error": None}
    carpeta = ROOT / "resultados" / "acciones_outlook" / informe["run_id"]
    salida = 1
    try:
        config = leer_config(validar_identidad=False)
        buzon = uuid_real(os.getenv("COURSE_MAILBOX_USER_ID", ""))
        informe["buzon_id"] = buzon
        destinatario = os.getenv("COURSE_TEST_RECIPIENT", "").strip()
        cliente = crear_cliente(config, "apponly")
        carpeta.mkdir(parents=True, exist_ok=True)

        def proveedor():
            return obtener_token(cliente, "apponly", informe["run_id"], informe["auth"], False)

        with ClienteOutlook(config, proveedor) as graph:
            informe["http"] = graph.historial
            informe["resultado"] = ejecutar(graph, buzon, args, carpeta, destinatario)
        resultado = informe["resultado"]
        incompleto = resultado.get("completo") is False or any(
            x["estado"] != "descargado" for x in resultado.get("descargas", [])
        )
        salida = 2 if incompleto else 0
    except requests.RequestException as error:
        informe["error"] = f"red_auth_{type(error).__name__}"
    except (RuntimeError, ValueError, TypeError, AttributeError) as error:
        informe["error"] = error.como_dict() if hasattr(error, "como_dict") else "entrada_o_condiciones_invalidas"
    except OSError:
        informe["error"] = "archivo_no_disponible"
    informe["exit_code"] = salida
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "auditoria.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        print("No se pudo guardar la evidencia de la operación.")
        return 1
    print(f"Operación: {args.operacion}; exit_code={salida}; carpeta={carpeta}")
    return salida


if __name__ == "__main__":
    raise SystemExit(main())
