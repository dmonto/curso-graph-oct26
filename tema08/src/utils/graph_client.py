import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from uuid import uuid4

import requests

from src.utils.auth_msal import ErrorAutenticacion, codigo_seguro, identificador_seguro

LOG = logging.getLogger("curso_graph.http")


class ErrorGraph(RuntimeError):
    def __init__(self, codigo, status=None, incierto=False):
        self.codigo = codigo_seguro(codigo)
        self.status = status
        self.incierto = incierto
        super().__init__(f"Graph: {self.codigo}; HTTP={status}; incierto={incierto}")

    def como_dict(self):
        return {"codigo": self.codigo, "http_status": self.status, "incierto": self.incierto}


def espera_reintento(respuesta, intento):
    valor = respuesta.headers.get("Retry-After", "").strip() if respuesta is not None else ""
    if valor.isdecimal() and len(valor) <= 10:
        return float(valor)
    if valor:
        try:
            fecha = parsedate_to_datetime(valor)
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            return max(0.0, (fecha - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            pass
    return 2 ** (intento - 1) + random.uniform(0, 0.25)


class ClienteGraph:
    def __init__(self, config, proveedor_token, max_intentos=3, presupuesto_espera=30):
        self.base = config.graph_api_url
        self.timeout = config.timeout_seconds
        self.proveedor_token = proveedor_token
        self.max_intentos = max_intentos
        self.presupuesto_espera = presupuesto_espera
        self.sesion = requests.Session()
        self.historial = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.sesion.close()

    def url_segura(self, ruta):
        url = self.base + ruta if ruta.startswith("/") else ruta
        try:
            partes = urlsplit(url)
            puerto = partes.port
        except ValueError:
            raise ErrorGraph("enlace_no_permitido") from None
        if (
            partes.scheme != "https" or partes.hostname != "graph.microsoft.com"
            or puerto not in (None, 443) or partes.username or partes.password
            or partes.fragment or not partes.path.startswith("/v1.0/")
        ):
            raise ErrorGraph("enlace_no_permitido")
        return url

    def peticion(self, metodo, ruta, params=None, cuerpo=None, headers=None):
        metodo = metodo.upper()
        url = self.url_segura(ruta)
        limite = self.max_intentos if metodo == "GET" else 1
        esperado = {200} if metodo == "GET" else {204}
        espera_total = 0.0
        for intento in range(1, limite + 1):
            try:
                token = self.proveedor_token()
            except (ErrorAutenticacion, requests.RequestException, ValueError):
                raise ErrorGraph("autenticacion_fallida") from None
            cabeceras = {"Accept": "application/json", **(headers or {})}
            cabeceras["Authorization"] = f"Bearer {token}"
            cabeceras["client-request-id"] = str(uuid4())
            registro = {
                "metodo": metodo, "ruta": urlsplit(url).path, "intento": intento,
                "client_request_id": cabeceras["client-request-id"],
                "request_id": None, "http_status": None, "error": None,
            }
            self.historial.append(registro)
            inicio = time.perf_counter()
            respuesta = None
            datos = None
            reintentable = False
            try:
                respuesta = self.sesion.request(
                    metodo, url, headers=cabeceras, params=params, json=cuerpo,
                    timeout=self.timeout, allow_redirects=False,
                )
                registro["http_status"] = respuesta.status_code
                registro["request_id"] = identificador_seguro(respuesta.headers.get("request-id"))
                if respuesta.status_code != 204:
                    try:
                        datos = respuesta.json()
                    except ValueError:
                        datos = None
                if respuesta.status_code not in esperado:
                    error = datos.get("error") if isinstance(datos, dict) else None
                    codigo = error.get("code") if isinstance(error, dict) else None
                    registro["error"] = codigo_seguro(codigo)
                    reintentable = respuesta.status_code in {429, 503}
            except requests.exceptions.SSLError:
                registro["error"] = "tls_graph"
            except requests.RequestException as error:
                registro["error"] = f"red_{type(error).__name__}"
                reintentable = isinstance(error, (requests.Timeout, requests.ConnectionError))
            finally:
                registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)
                LOG.info(
                    "evento=http metodo=%s intento=%s http_status=%s "
                    "client_request_id=%s request_id=%s",
                    metodo, intento, registro["http_status"],
                    registro["client_request_id"], registro["request_id"],
                )
            if registro["error"] is None:
                if registro["http_status"] == 204:
                    return None
                if not isinstance(datos, dict):
                    registro["error"] = "json_invalido"
                    raise ErrorGraph("json_invalido", registro["http_status"])
                return datos
            if metodo == "GET" and reintentable and intento < limite:
                espera = espera_reintento(respuesta, intento)
                if espera_total + espera > self.presupuesto_espera:
                    raise ErrorGraph("reintento_aplazado", registro["http_status"])
                registro["espera_segundos"] = round(espera, 2)
                time.sleep(espera)
                espera_total += espera
                continue
            incierto = metodo != "GET" and (
                registro["http_status"] is None or registro["http_status"] >= 500
            )
            raise ErrorGraph(registro["error"], registro["http_status"], incierto)

    def listar(self, ruta, params=None, headers=None, max_paginas=100):
        if max_paginas < 1:
            raise ValueError("max_paginas debe ser positivo.")
        resultado = {"elementos": [], "paginas": 0, "completo": False, "error": None}
        url = self.url_segura(ruta)
        visitadas = set()
        try:
            while url:
                if resultado["paginas"] >= max_paginas:
                    raise ErrorGraph("limite_paginas")
                if url in visitadas:
                    raise ErrorGraph("paginacion_circular")
                visitadas.add(url)
                pagina = self.peticion("GET", url, params=params, headers=headers)
                elementos = pagina.get("value")
                if not isinstance(elementos, list) or any(
                    not isinstance(x, dict) or not isinstance(x.get("id"), str)
                    or not x["id"] for x in elementos
                ):
                    raise ErrorGraph("coleccion_invalida", 200)
                resultado["elementos"].extend(elementos)
                resultado["paginas"] += 1
                siguiente = pagina.get("@odata.nextLink")
                if siguiente is not None and not isinstance(siguiente, str):
                    raise ErrorGraph("nextlink_invalido", 200)
                url = self.url_segura(siguiente) if siguiente else None
                params = None
            resultado["completo"] = True
        except ErrorGraph as error:
            resultado["error"] = error.como_dict()
        return resultado
