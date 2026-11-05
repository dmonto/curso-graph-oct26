import argparse
import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from uuid import uuid4

from src.lab_archivos import ARCHIVO_DEMO, CARPETA_DEMO, DRIVE_DEMO, ArchivosLocales
from src.utils.auth_msal import ErrorAutenticacion
from src.utils.config import leer_config
from src.utils.files_client import (
    UNIDAD,
    cliente_archivos,
    nombre_archivo,
    ruta_item,
    segmento,
    url_https,
)
from src.utils.graph_client import ErrorGraph


def guardar_json(destino, datos):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def metadatos(item):
    campos = ("id", "name", "size", "eTag", "cTag", "webUrl", "parentReference",
              "file", "folder", "lastModifiedDateTime")
    return {campo: item[campo] for campo in campos if campo in item}


def permiso_visible(permiso):
    enlace = permiso.get("link") or {}
    return {"id": permiso.get("id"), "roles": permiso.get("roles", []),
            "tipo_enlace": enlace.get("type"), "ambito": enlace.get("scope"),
            "expirationDateTime": permiso.get("expirationDateTime"),
            "herencia": "confirmada" if permiso.get("inheritedFrom") else "verificar_origen",
            "inheritedFrom": permiso.get("inheritedFrom")}


def auditar_permisos(cliente, drive_id, item_id):
    lectura = cliente.listar(ruta_item(drive_id, item_id) + "/permissions")
    lectura["elementos"] = [permiso_visible(x) for x in lectura["elementos"]]
    lectura["alcance"] = "permisos_comparticion_visibles_para_el_solicitante"
    lectura["alertas"] = [x["id"] for x in lectura["elementos"] if x["ambito"] == "anonymous"]
    return lectura


@contextmanager
def abrir_archivos(local, escritura, informe, parcial=False):
    if local:
        with ArchivosLocales(parcial) as cliente:
            yield cliente, DRIVE_DEMO, CARPETA_DEMO
    else:
        config = leer_config()
        drive_id = os.getenv("DRIVE_ID", "")
        folder_id = os.getenv("FOLDER_ID", "")
        segmento(drive_id)
        segmento(folder_id)
        scopes = ["Files.ReadWrite.All" if escritura else "Files.Read.All"]
        with cliente_archivos(config, scopes, informe) as cliente:
            yield cliente, drive_id, folder_id


def comprobar_carpeta_curso(cliente, drive_id, folder_id):
    carpeta = cliente.peticion("GET", ruta_item(drive_id, folder_id))
    nombre = carpeta.get("name", "")
    if ("folder" not in carpeta or carpeta.get("id") != folder_id
            or carpeta.get("parentReference", {}).get("driveId") != drive_id
            or not (nombre == "CursoGraph" or nombre.startswith("CURSO-"))):
        raise ValueError("Configura una carpeta de laboratorio CursoGraph o CURSO-.")
    return carpeta


def inventario(cliente, drive_id, folder_id, max_paginas=100):
    lectura = cliente.listar(ruta_item(drive_id, folder_id) + "/children", params={
        "$select": "id,name,size,eTag,webUrl,parentReference,file,folder", "$top": 2},
        max_paginas=max_paginas)
    lectura["elementos"] = [metadatos(x) for x in lectura["elementos"]]
    return lectura


def publicar_archivos(cliente, drive_id, folder_id, archivos, informe, fragmentos=False):
    comprobar_carpeta_curso(cliente, drive_id, folder_id)
    archivos = [Path(x) for x in archivos]
    if not archivos or any(not x.is_file() for x in archivos):
        raise ValueError("Debes proporcionar archivos locales existentes.")
    if len({x.name for x in archivos}) != len(archivos):
        raise ValueError("Los nombres del paquete deben ser diferentes.")
    for archivo in archivos:
        nombre_archivo(archivo.name)
    carpeta = cliente.crear_carpeta(drive_id, folder_id, "CURSO-" + informe["run_id"])
    informe["carpeta_ejecucion"] = metadatos(carpeta)
    informe["archivos"] = []
    for archivo in archivos:
        subir = cliente.subir_fragmentos if fragmentos else cliente.subir_simple
        # 320 KiB en esta práctica para ver varios fragmentos en un archivo pequeño.
        if fragmentos:
            item = subir(drive_id, carpeta["id"], archivo, tamano=UNIDAD)
        else:
            item = subir(drive_id, carpeta["id"], archivo)
        informe["archivos"].append(metadatos(item))
    informe["permisos"] = auditar_permisos(cliente, drive_id, carpeta["id"])
    informe["cargas_confirmadas"] = True
    informe["completo"] = informe["permisos"]["completo"]
    return informe["archivos"]


def enlace_organizacion(cliente, drive_id, item_id):
    expiracion = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
    expiracion = expiracion.replace("+00:00", "Z")
    respuesta = cliente.escribir("POST", ruta_item(drive_id, item_id) + "/createLink", cuerpo={
        "type": "view", "scope": "organization", "expirationDateTime": expiracion,
        "retainInheritedPermissions": True}, esperados=(200, 201))
    resumen = permiso_visible(respuesta)
    resumen["expiracion_solicitada"] = expiracion
    resumen["verificar"] = (resumen["ambito"] != "organization"
                            or resumen["tipo_enlace"] != "view"
                            or resumen["roles"] != ["read"]
                            or resumen["expirationDateTime"] != expiracion)
    return resumen


def renombrar_con_etag(cliente, drive_id, item, nuevo_nombre, etag):
    nombre_archivo(nuevo_nombre)
    try:
        actualizado = cliente.escribir("PATCH", ruta_item(drive_id, item["id"]),
            cuerpo={"name": nuevo_nombre}, headers={"If-Match": etag}, esperados=(200,))
        return {"estado": "actualizado", "item": metadatos(actualizado)}
    except ErrorGraph as error:
        if error.status != 412:
            raise
        actual = cliente.peticion("GET", ruta_item(drive_id, item["id"]))
        return {"estado": "conflicto_requiere_revision", "error": error.como_dict(),
                "etag_propuesto": etag, "item_actual": metadatos(actual),
                "nombre_propuesto": nuevo_nombre, "reintento_automatico": False}


def borrador_teams(item, completo):
    url = url_https(item.get("webUrl"))
    estado = "Archivos cargados" if completo else "Carga pendiente de revisión"
    contenido = (f"<p>{estado}.</p><p><a href='{escape(url, quote=True)}'>"
                 f"{escape(item.get('name', 'Informe'))}</a></p>")
    return {"body": {"contentType": "html", "content": contenido}}


def ejecutar(args, informe):
    escritura = args.accion in {"subir", "conflicto", "enlace"}
    with abrir_archivos(args.local, escritura, informe, args.parcial) as (cliente, drive_id, folder_id):
        try:
            informe["destino"] = {"drive_id": drive_id, "folder_id": folder_id}
            if args.accion == "listar":
                informe["lectura"] = inventario(cliente, drive_id, folder_id, args.max_paginas)
                informe["completo"] = informe["lectura"]["completo"]
            elif args.accion == "buscar":
                consulta = segmento(args.consulta.replace("'", "''"))
                ruta = ruta_item(drive_id, folder_id) + f"/search(q='{consulta}')"
                lectura = cliente.listar(ruta)
                lectura["elementos"] = [metadatos(x) for x in lectura["elementos"]]
                informe["lectura"] = lectura
                informe["completo"] = lectura["completo"]
            elif args.accion == "carpeta-canal":
                team = os.getenv("TEAM_ID", "") if not args.local else "EQUIPO-DEMO"
                canal = os.getenv("CHANNEL_ID", "") if not args.local else "19:CURSO-DEMO"
                carpeta = cliente.peticion("GET", f"/teams/{segmento(team)}/channels/{segmento(canal)}/filesFolder")
                informe["carpeta_canal"] = metadatos(carpeta)
                informe["completo"] = True
            elif args.accion == "permisos":
                informe["permisos"] = auditar_permisos(cliente, drive_id, args.item_id or folder_id)
                informe["completo"] = informe["permisos"]["completo"]
            elif args.accion in {"versiones", "descargar"}:
                item_id = args.item_id or (ARCHIVO_DEMO if args.local else "")
                segmento(item_id)
                if args.accion == "versiones":
                    informe["lectura"] = cliente.listar(ruta_item(drive_id, item_id) + "/versions")
                    informe["completo"] = informe["lectura"]["completo"]
                else:
                    informe["descarga"] = cliente.descargar(drive_id, item_id, args.salida / "descargado.csv")
                    informe["completo"] = True
            else:
                fuente = args.salida / "informe.csv"
                fuente.parent.mkdir(parents=True, exist_ok=True)
                fuente.write_text("categoria;pendientes\nproveedores;3\ncentros;2\n", encoding="utf-8")
                archivos = [fuente]
                if args.fragmentos:
                    grande = args.salida / "datos-demo.bin"
                    grande.write_bytes(b"X" * (2 * UNIDAD + 17))
                    archivos.append(grande)
                items = publicar_archivos(cliente, drive_id, folder_id, archivos, informe, args.fragmentos)
                if args.accion == "conflicto":
                    informe["renombrado"] = renombrar_con_etag(
                        cliente, drive_id, items[0], "informe-revisado.csv", '"ETAG-OBSOLETO"')
                if args.accion == "enlace":
                    if not args.local and not args.crear_enlace_organizacion:
                        raise ValueError("La creación real del enlace requiere --crear-enlace-organizacion.")
                    informe["enlace"] = enlace_organizacion(cliente, drive_id, items[0]["id"])
                informe["mensaje_teams"] = borrador_teams(items[0], informe["completo"])
        finally:
            informe["http"] = cliente.historial


def main():
    parser = argparse.ArgumentParser(description="Laboratorio de archivos de Microsoft Graph.")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--parcial", action="store_true", help="Simula una lectura local interrumpida.")
    parser.add_argument("--accion", choices=["listar", "buscar", "permisos", "versiones", "descargar",
                                          "subir", "enlace", "conflicto", "carpeta-canal"], default="listar")
    parser.add_argument("--consulta", default="proveedores")
    parser.add_argument("--item-id")
    parser.add_argument("--max-paginas", type=int, default=100)
    parser.add_argument("--fragmentos", action="store_true")
    parser.add_argument("--crear-enlace-organizacion", action="store_true")
    parser.add_argument("--salida", type=Path, default=Path("output/tema8"))
    args = parser.parse_args()
    informe = {"run_id": str(uuid4()), "local": args.local, "auth": [], "completo": False}
    try:
        if args.parcial and not args.local:
            raise ValueError("--parcial es una opción de simulación local.")
        if args.accion == "enlace" and not args.local and not args.crear_enlace_organizacion:
            raise ValueError("Añade --crear-enlace-organizacion para esa operación real.")
        ejecutar(args, informe)
    except ErrorGraph as error:
        informe["error"] = error.como_dict()
        informe["completo"] = False
    except ErrorAutenticacion:
        informe["error"] = {"codigo": "autenticacion_fallida"}
        informe["completo"] = False
    except (ValueError, OSError) as error:
        informe["error"] = {"codigo": type(error).__name__}
        informe["completo"] = False
        print("Revisa argumentos, archivos y configuración local.")
    finally:
        guardar_json(args.salida / "resultado.json", informe)
    print(args.salida / "resultado.json")
    return 0 if informe["completo"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
