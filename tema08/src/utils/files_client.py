import hashlib
import mimetypes
import time
from pathlib import Path
from urllib.parse import quote, urlsplit
from uuid import uuid4

import requests

from src.utils.auth_msal import (
    ErrorAutenticacion,
    codigo_seguro,
    crear_cliente,
    identificador_seguro,
)
from src.utils.graph_client import ClienteGraph, ErrorGraph, espera_reintento
from src.utils.teams_client import token_delegado_teams as token_delegado

UNIDAD = 320 * 1024
FRAGMENTO = 10 * UNIDAD
LIMITE_SIMPLE_LAB = 2 * 1024 * 1024


def segmento(valor):
    if not isinstance(valor, str) or not valor or any(ord(c) < 32 for c in valor):
        raise ValueError("Identificador vacío o inválido.")
    return quote(valor, safe="")


def nombre_archivo(valor):
    if (not isinstance(valor, str) or not valor or len(valor) > 120
            or valor in {".", ".."} or valor.startswith("~") or valor.endswith((".", " "))
            or any(c in '/\\*<>?:|#%"' or ord(c) < 32 for c in valor)):
        raise ValueError("Nombre no admitido en el laboratorio.")
    return segmento(valor)


def ruta_item(drive_id, item_id):
    return f"/drives/{segmento(drive_id)}/items/{segmento(item_id)}"


def url_https(valor):
    try:
        partes = urlsplit(valor)
        puerto = partes.port
    except (ValueError, TypeError):
        raise ErrorGraph("url_transferencia_invalida") from None
    if (partes.scheme != "https" or not partes.hostname or puerto not in (None, 443)
            or partes.username or partes.password or partes.fragment):
        raise ErrorGraph("url_transferencia_invalida")
    return valor


class ClienteArchivos(ClienteGraph):
    def __init__(self, config, proveedor_token):
        super().__init__(config, proveedor_token)
        self.transferencias = requests.Session()
        self.transferencias.trust_env = False
        self.transferencias.auth = None

    def __exit__(self, *args):
        self.transferencias.close()
        super().__exit__(*args)

    def escribir(self, metodo, ruta, cuerpo=None, datos=None, params=None,
                 headers=None, esperados=(200, 201)):
        if metodo not in {"POST", "PATCH", "PUT", "DELETE"}:
            raise ValueError("Método no admitido.")
        url = self.url_segura(ruta)
        try:
            token = self.proveedor_token()
        except (ErrorAutenticacion, requests.RequestException, ValueError):
            raise ErrorGraph("autenticacion_fallida") from None
        cabeceras = {"Accept": "application/json", **(headers or {}),
                     "Authorization": f"Bearer {token}", "client-request-id": str(uuid4())}
        registro = {"metodo": metodo, "ruta": urlsplit(url).path, "http_status": None,
                    "client_request_id": cabeceras["client-request-id"], "error": None}
        self.historial.append(registro)
        inicio = time.perf_counter()
        try:
            with self.sesion.request(metodo, url, json=cuerpo, data=datos, params=params,
                    headers=cabeceras, timeout=self.timeout, allow_redirects=False) as respuesta:
                registro["http_status"] = respuesta.status_code
                registro["request_id"] = identificador_seguro(respuesta.headers.get("request-id"))
                if respuesta.status_code in {429, 503}:
                    registro["espera_recomendada_segundos"] = espera_reintento(respuesta, 1)
                return self._resultado(respuesta, esperados, escritura=True)
        except requests.RequestException:
            registro["error"] = "red_escritura"
            raise ErrorGraph("red_escritura", registro["http_status"], True) from None
        except ErrorGraph as error:
            registro["error"] = error.codigo
            raise
        finally:
            registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)

    @staticmethod
    def _resultado(respuesta, esperados, escritura=False):
        if respuesta.status_code == 204 and 204 in esperados:
            return None
        try:
            datos = respuesta.json()
        except ValueError:
            datos = None
        if respuesta.status_code not in esperados:
            error = datos.get("error", {}) if isinstance(datos, dict) else {}
            codigo = error.get("code") if isinstance(error, dict) else None
            raise ErrorGraph(codigo_seguro(codigo), respuesta.status_code,
                             escritura and respuesta.status_code >= 500)
        if not isinstance(datos, dict):
            raise ErrorGraph("json_invalido", respuesta.status_code, escritura)
        return datos

    def transferir_json(self, metodo, url, datos=None, headers=None, esperados=(200,)):
        # La URL debe proceder de Graph; se mantiene solo en memoria.
        url_https(url)
        if any(campo.lower() == "authorization" for campo in (headers or {})):
            raise ValueError("La transferencia preautorizada no lleva Authorization.")
        registro = {"operacion": "fragmento" if metodo == "PUT" else "estado_sesion",
                    "http_status": None, "error": None}
        self.historial.append(registro)
        try:
            with self.transferencias.request(metodo, url, data=datos, headers=headers or {},
                    timeout=self.timeout, allow_redirects=False) as respuesta:
                registro["http_status"] = respuesta.status_code
                if respuesta.status_code in {429, 503}:
                    registro["espera_recomendada_segundos"] = espera_reintento(respuesta, 1)
                return respuesta.status_code, self._resultado(
                    respuesta, esperados, escritura=metodo == "PUT")
        except requests.RequestException:
            registro["error"] = "red_transferencia"
            raise ErrorGraph("red_transferencia", registro["http_status"], metodo == "PUT") from None
        except ErrorGraph as error:
            registro["error"] = error.codigo
            raise

    def crear_carpeta(self, drive_id, parent_id, nombre):
        nombre_archivo(nombre)
        return self.escribir("POST", ruta_item(drive_id, parent_id) + "/children",
            cuerpo={"name": nombre, "folder": {}, "@microsoft.graph.conflictBehavior": "fail"},
            esperados=(201,))

    def subir_simple(self, drive_id, parent_id, archivo):
        archivo = Path(archivo)
        if archivo.stat().st_size > LIMITE_SIMPLE_LAB:
            raise ValueError("El laboratorio limita la subida simple a 2 MiB.")
        contenido = archivo.read_bytes()
        if len(contenido) > LIMITE_SIMPLE_LAB:
            raise ValueError("El archivo cambió de tamaño.")
        ruta = ruta_item(drive_id, parent_id) + f":/{nombre_archivo(archivo.name)}:/content"
        tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
        return self.escribir("PUT", ruta, datos=contenido,
            params={"@microsoft.graph.conflictBehavior": "fail"},
            headers={"Content-Type": tipo}, esperados=(200, 201))

    def subir_fragmentos(self, drive_id, parent_id, archivo, tamano=FRAGMENTO):
        if tamano <= 0 or tamano % UNIDAD or tamano >= 60 * 1024 * 1024:
            raise ValueError("Fragmento: múltiplo de 320 KiB y menor que 60 MiB.")
        archivo = Path(archivo)
        total = archivo.stat().st_size
        if total == 0:
            return self.subir_simple(drive_id, parent_id, archivo)
        ruta = ruta_item(drive_id, parent_id) + f":/{nombre_archivo(archivo.name)}:/createUploadSession"
        # El nombre ya va en la ruta; repetirlo en el cuerpo puede provocar 400 invalidRequest.
        sesion = self.escribir("POST", ruta, cuerpo={"item": {
            "@microsoft.graph.conflictBehavior": "fail"}}, esperados=(200,))
        url = url_https(sesion.get("uploadUrl"))
        inicio = 0
        with archivo.open("rb") as fichero:
            while inicio < total:
                bloque = fichero.read(min(tamano, total - inicio))
                if not bloque or len(bloque) != min(tamano, total - inicio):
                    raise ErrorGraph("archivo_local_cambio")
                fin = inicio + len(bloque) - 1
                estado, datos = self.transferir_json("PUT", url, datos=bloque, headers={
                    "Content-Length": str(len(bloque)),
                    "Content-Range": f"bytes {inicio}-{fin}/{total}"}, esperados=(200, 201, 202))
                if estado in {200, 201}:
                    if fin != total - 1 or not datos.get("id"):
                        raise ErrorGraph("confirmacion_subida_invalida", estado, True)
                    return datos
                inicio = fin + 1
                if inicio >= total or datos.get("nextExpectedRanges") != [f"{inicio}-"]:
                    raise ErrorGraph("revisar_estado_sesion", 202, True)
        raise ErrorGraph("subida_no_confirmada", incierto=True)

    def descargar(self, drive_id, item_id, destino, limite=10 * 1024 * 1024):
        item = self.peticion("GET", ruta_item(drive_id, item_id), params={
            "$select": "id,file,size,@microsoft.graph.downloadUrl"})
        if ("file" not in item or not isinstance(item.get("size"), int)
                or item["size"] < 0 or item["size"] > limite):
            raise ValueError("Archivo inválido o superior al límite local.")
        url = url_https(item.get("@microsoft.graph.downloadUrl"))
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_name(destino.name + "." + uuid4().hex + ".part")
        resumen = hashlib.sha256()
        total = 0
        try:
            with self.transferencias.get(url, stream=True, timeout=self.timeout,
                                        allow_redirects=False) as respuesta:
                if respuesta.status_code != 200:
                    raise ErrorGraph("descarga_no_disponible", respuesta.status_code)
                with temporal.open("xb") as fichero:
                    for bloque in respuesta.iter_content(64 * 1024):
                        if not bloque:
                            continue
                        total += len(bloque)
                        if total > limite:
                            raise ValueError("Descarga superior al límite local.")
                        resumen.update(bloque)
                        fichero.write(bloque)
            if total != item["size"]:
                raise ErrorGraph("descarga_incompleta")
            temporal.replace(destino)
            return {"bytes": total, "sha256": resumen.hexdigest(), "destino": str(destino)}
        except requests.RequestException:
            raise ErrorGraph("red_descarga") from None
        finally:
            temporal.unlink(missing_ok=True)


def cliente_archivos(config, scopes, informe):
    msal = crear_cliente(config, "delegada")
    return ClienteArchivos(config, lambda: token_delegado(
        msal, scopes, informe["run_id"], informe["auth"]))
