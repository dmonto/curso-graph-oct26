import hashlib
import time
from urllib.parse import urlsplit
from uuid import uuid4

import requests

from src.utils.auth_msal import ErrorAutenticacion, codigo_seguro, identificador_seguro
from src.utils.graph_client import ClienteGraph, ErrorGraph, espera_reintento

PREFER = {"Prefer": 'IdType="ImmutableId", outlook.timezone="UTC"'}


class ClienteOutlook(ClienteGraph):
    def iniciar(self, metodo, ruta, headers=None):
        url = self.url_segura(ruta)
        try:
            token = self.proveedor_token()
        except (ErrorAutenticacion, requests.RequestException, ValueError):
            raise ErrorGraph("autenticacion_fallida") from None
        cabeceras = {"Accept": "application/json", **PREFER, **(headers or {})}
        cabeceras["Authorization"] = f"Bearer {token}"
        cabeceras["client-request-id"] = str(uuid4())
        registro = {"metodo": metodo, "ruta": urlsplit(url).path, "intento": 1,
                    "client_request_id": cabeceras["client-request-id"],
                    "request_id": None, "http_status": None, "error": None}
        self.historial.append(registro)
        return url, cabeceras, registro

    def escribir(self, metodo, ruta, cuerpo=None, esperados=(204,), headers=None):
        if metodo not in {"POST", "PATCH", "DELETE"}:
            raise ValueError("Método de escritura no admitido.")
        url, cabeceras, registro = self.iniciar(metodo, ruta, headers)
        inicio = time.perf_counter()
        try:
            respuesta = self.sesion.request(metodo, url, headers=cabeceras, json=cuerpo,
                                             timeout=self.timeout, allow_redirects=False)
            registro["http_status"] = respuesta.status_code
            registro["request_id"] = identificador_seguro(respuesta.headers.get("request-id"))
            datos = None
            if respuesta.status_code not in {202, 204}:
                try:
                    datos = respuesta.json()
                except ValueError:
                    pass
            if respuesta.status_code not in esperados:
                detalle = datos.get("error", {}) if isinstance(datos, dict) else {}
                codigo = detalle.get("code") if isinstance(detalle, dict) else None
                raise ErrorGraph(codigo_seguro(codigo), respuesta.status_code,
                                 respuesta.status_code >= 500)
            if respuesta.status_code in {202, 204}:
                return None
            if not isinstance(datos, dict):
                raise ErrorGraph("json_invalido", respuesta.status_code, True)
            return datos
        except requests.RequestException as error:
            registro["error"] = f"red_{type(error).__name__}"
            raise ErrorGraph(registro["error"], registro["http_status"], True) from None
        except ErrorGraph as error:
            registro["error"] = error.codigo
            raise
        finally:
            registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)

    def descargar(self, ruta, destino, max_bytes=2 * 1024 * 1024):
        if max_bytes <= 0:
            raise ValueError("El límite de descarga debe ser positivo.")
        url, cabeceras, registro = self.iniciar("GET", ruta)
        cabeceras["Accept"] = "application/octet-stream"
        temporal = destino.with_suffix(destino.suffix + ".part")
        creado = False
        total = 0
        digest = hashlib.sha256()
        inicio = time.perf_counter()
        try:
            with self.sesion.request("GET", url, headers=cabeceras, timeout=self.timeout,
                                     stream=True, allow_redirects=False) as respuesta:
                registro["http_status"] = respuesta.status_code
                registro["request_id"] = identificador_seguro(respuesta.headers.get("request-id"))
                if respuesta.status_code != 200:
                    if respuesta.status_code in {429, 503}:
                        registro["espera_recomendada_segundos"] = espera_reintento(respuesta, 1)
                    raise ErrorGraph(f"HTTP_{respuesta.status_code}", respuesta.status_code)
                longitud = respuesta.headers.get("Content-Length", "")
                if longitud.isdecimal() and int(longitud) > max_bytes:
                    raise ErrorGraph("limite_adjunto", 200)
                with temporal.open("xb") as archivo:
                    creado = True
                    for bloque in respuesta.iter_content(chunk_size=64 * 1024):
                        if not bloque:
                            continue
                        total += len(bloque)
                        if total > max_bytes:
                            raise ErrorGraph("limite_adjunto", 200)
                        archivo.write(bloque)
                        digest.update(bloque)
            temporal.replace(destino)
            return {"archivo": destino.name, "bytes": total, "sha256": digest.hexdigest()}
        except requests.RequestException as error:
            registro["error"] = f"red_{type(error).__name__}"
            raise ErrorGraph(registro["error"], registro["http_status"]) from None
        except ErrorGraph as error:
            registro["error"] = error.codigo
            raise
        except OSError:
            registro["error"] = "archivo_no_disponible"
            raise
        finally:
            if creado and temporal.exists():
                temporal.unlink()
            registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)
