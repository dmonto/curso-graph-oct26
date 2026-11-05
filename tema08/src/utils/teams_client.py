import time
from urllib.parse import urlsplit
from uuid import uuid4

import requests

from src.utils.auth_msal import (
    ERRORES_INTERACTIVOS,
    ErrorAutenticacion,
    codigo_seguro,
    crear_cliente,
    exigir_token,
    identificador_seguro,
    invocar_msal,
    registrar_resultado,
)
from src.utils.graph_client import ClienteGraph, ErrorGraph, espera_reintento


def token_delegado_teams(cliente, scopes, run_id, historial, permitir_interaccion=True):
    inicio = time.perf_counter()
    cuentas = cliente.get_accounts()
    if len(cuentas) > 1:
        raise ErrorAutenticacion("seleccion_cuenta_requerida")
    if cuentas:
        resultado = invocar_msal(lambda: cliente.acquire_token_silent_with_error(
            scopes=scopes, account=cuentas[0]), run_id)
        if resultado is not None:
            registro = registrar_resultado(resultado, "silent_teams", run_id, historial, inicio)
            if registro["resultado"] == "token_obtenido":
                return exigir_token(resultado, registro)
            if registro["error"] not in ERRORES_INTERACTIVOS:
                return exigir_token(resultado, registro)
    if not permitir_interaccion:
        raise ErrorAutenticacion("interaccion_requerida")
    inicio = time.perf_counter()
    print("Se abrirá el navegador para iniciar sesión...", flush=True)
    resultado = invocar_msal(lambda: cliente.acquire_token_interactive(
        scopes=scopes, prompt="select_account", timeout=300), run_id)
    registro = registrar_resultado(resultado, "interactivo_teams", run_id, historial, inicio)
    return exigir_token(resultado, registro)


class ClienteTeams(ClienteGraph):
    def escribir(self, metodo, ruta, cuerpo=None, esperado=201):
        if metodo not in {"POST", "PATCH", "DELETE"}:
            raise ValueError("Método de escritura no admitido.")
        url = self.url_segura(ruta)
        try:
            token = self.proveedor_token()
        except (ErrorAutenticacion, requests.RequestException, ValueError):
            raise ErrorGraph("autenticacion_fallida") from None
        client_id = str(uuid4())
        registro = {"metodo": metodo, "ruta": urlsplit(url).path, "intento": 1,
                    "client_request_id": client_id, "request_id": None,
                    "http_status": None, "error": None}
        self.historial.append(registro)
        inicio = time.perf_counter()
        try:
            respuesta = self.sesion.request(metodo, url, json=cuerpo,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json",
                         "client-request-id": client_id}, timeout=self.timeout, allow_redirects=False)
            registro["http_status"] = respuesta.status_code
            registro["request_id"] = identificador_seguro(respuesta.headers.get("request-id"))
            if respuesta.status_code in {429, 503}:
                registro["espera_recomendada_segundos"] = espera_reintento(respuesta, 1)
            datos = None
            if respuesta.status_code != 204:
                try:
                    datos = respuesta.json()
                except ValueError:
                    pass
            if respuesta.status_code != esperado:
                error = datos.get("error", {}) if isinstance(datos, dict) else {}
                codigo = error.get("code") if isinstance(error, dict) else None
                raise ErrorGraph(codigo_seguro(codigo), respuesta.status_code, respuesta.status_code >= 500)
            if esperado == 204:
                return None
            if not isinstance(datos, dict):
                raise ErrorGraph("json_invalido", esperado, True)
            return datos
        except requests.RequestException as error:
            registro["error"] = f"red_{type(error).__name__}"
            raise ErrorGraph(registro["error"], registro["http_status"], True) from None
        except ErrorGraph as error:
            registro["error"] = error.codigo
            raise
        finally:
            registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)


def cliente_autenticado(config, scopes, informe, permitir_interaccion=True):
    msal = crear_cliente(config, "delegada")
    return ClienteTeams(config, lambda: token_delegado_teams(
        msal, scopes, informe["run_id"], informe["auth"], permitir_interaccion))
