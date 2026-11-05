import json
from collections import Counter
from html import escape
from urllib.parse import urlsplit

from src.auditar_directorio import uuid_real


def enlace_documento(url):
    partes = urlsplit(url)
    if (partes.scheme != "https" or not partes.hostname
            or not partes.hostname.endswith(".sharepoint.com")
            or partes.username or partes.password or partes.port not in {None, 443}):
        raise ValueError("Utiliza la URL HTTPS de un documento del SharePoint de prácticas.")
    return url


def mensaje_resumen(propuestas, lectura_completa, enlace):
    enlace = enlace_documento(enlace)
    estados = Counter(x["estado"] for x in propuestas)
    listas = [x for x in propuestas if x["estado"] == "listo_para_revision"] if lectura_completa else []
    pendientes = len(propuestas) - len(listas)
    filas = "".join(f"<li>{escape(x['caso'])}: {escape(x['titulo'])}</li>" for x in listas)
    alcance = "completa" if lectura_completa else "parcial; cifras de los elementos observados"
    contenido = ("<p><strong>CURSO-Resumen de solicitudes y agenda</strong></p>"
                 f"<p>Lectura: {alcance}. Observadas: {len(propuestas)}. "
                 f"Listas para revisión: {len(listas)}. Pendientes: {pendientes}.</p>"
                 f"<ul>{filas}</ul><p><a href=\"{escape(enlace, quote=True)}\">Abrir informe</a></p>")
    return {"body": {"contentType": "html", "content": contenido}}, {
        "observadas": len(propuestas), "listas": len(listas), "pendientes": pendientes,
        "lectura_completa": lectura_completa, "estados_origen": dict(estados)}


def mensaje_con_mencion(usuario_id, nombre):
    usuario_id = uuid_real(usuario_id)
    return {"body": {"contentType": "html", "content":
            f'<p>CURSO-Revisión pendiente para <at id="0">{escape(nombre)}</at>.</p>'},
            "mentions": [{"id": 0, "mentionText": nombre,
                          "mentioned": {"user": {"id": usuario_id, "displayName": nombre,
                                                 "userIdentityType": "aadUser"}}}]}


def mensaje_tarjeta(resumen, enlace):
    tarjeta = {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
               "type": "AdaptiveCard", "version": "1.2", "body": [
                   {"type": "TextBlock", "text": "CURSO-Estado de automatizaciones", "weight": "Bolder", "wrap": True},
                   {"type": "TextBlock", "text":
                    f"Observadas: {resumen['observadas']}; listas: {resumen['listas']}; pendientes: {resumen['pendientes']}.", "wrap": True},
                   {"type": "TextBlock", "text": "Lectura completa" if resumen["lectura_completa"]
                    else "Lectura parcial: requiere completar datos", "wrap": True}],
               "actions": [{"type": "Action.OpenUrl", "title": "Abrir informe", "url": enlace_documento(enlace)}]}
    return {"body": {"contentType": "html", "content": '<attachment id="estado-curso"></attachment>'},
            "attachments": [{"id": "estado-curso", "contentType": "application/vnd.microsoft.card.adaptive",
                             "contentUrl": None, "content": json.dumps(tarjeta, ensure_ascii=False)}]}


def validar_mensaje(payload):
    if not isinstance(payload, dict) or set(payload) - {"body", "mentions", "attachments"}:
        raise ValueError("Utiliza un chatMessage de prácticas.")
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > 16 * 1024:
        raise ValueError("El mensaje supera el límite local de 16 KiB.")
    cuerpo = payload.get("body", {})
    if cuerpo.get("contentType") not in {"text", "html"} or not isinstance(cuerpo.get("content"), str):
        raise ValueError("Se necesita un cuerpo text o html.")
    adjuntos = payload.get("attachments", [])
    menciones = payload.get("mentions", [])
    if not isinstance(adjuntos, list) or len(adjuntos) > 1 or not isinstance(menciones, list) or len(menciones) > 1:
        raise ValueError("El laboratorio utiliza como máximo una tarjeta y una mención.")
    marca = "CURSO-" in cuerpo["content"]
    for adjunto in adjuntos:
        if adjunto.get("contentType") != "application/vnd.microsoft.card.adaptive" or adjunto.get("contentUrl") is not None:
            raise ValueError("Utiliza la tarjeta de prácticas.")
        tarjeta = json.loads(adjunto["content"])
        if tarjeta.get("type") != "AdaptiveCard":
            raise ValueError("El adjunto necesita una AdaptiveCard.")
        marca = marca or "CURSO-" in adjunto["content"]
        if f'<attachment id="{adjunto["id"]}"></attachment>' not in cuerpo["content"]:
            raise ValueError("El ID de la tarjeta debe coincidir con el del cuerpo.")
    for mencion in menciones:
        numero = mencion["id"]
        if not isinstance(numero, int) or f'<at id="{numero}">' not in cuerpo["content"]:
            raise ValueError("El ID de mención debe coincidir con el del cuerpo.")
        uuid_real(mencion["mentioned"]["user"]["id"])
    if not marca:
        raise ValueError("El mensaje debe incluir la marca CURSO-.")
