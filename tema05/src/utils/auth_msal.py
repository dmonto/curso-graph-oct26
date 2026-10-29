import logging
import os
import re
import time
from uuid import UUID

import msal
import requests

LOG = logging.getLogger("curso_graph.auth")
SCOPES_DELEGADOS = ["https://graph.microsoft.com/User.Read"]
SCOPES_APLICACION = ["https://graph.microsoft.com/.default"]
ERRORES_INTERACTIVOS = {
    "interaction_required", "login_required", "consent_required", "invalid_grant"
}


class ErrorAutenticacion(RuntimeError):
    pass


def codigo_seguro(valor):
    if isinstance(valor, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", valor):
        return valor
    return "no_informado"


def identificador_seguro(valor):
    try:
        return str(UUID(str(valor)))
    except (ValueError, TypeError, AttributeError):
        return None


def uuid_variable(nombre):
    valor = os.getenv(nombre, "").strip()
    identificador = identificador_seguro(valor)
    if identificador is None or UUID(identificador).int == 0:
        raise RuntimeError(f"{nombre} debe contener un UUID real.")
    return identificador


def crear_cliente(config, modo, cache=None):
    tenant_id = uuid_variable("TENANT_ID")
    variable = "CLIENT_ID_APPONLY" if modo == "apponly" else "CLIENT_ID_DELEGATED"
    client_id = uuid_variable(variable)
    opciones = {
        "authority": f"https://login.microsoftonline.com/{tenant_id}",
        "token_cache": cache if cache is not None else msal.TokenCache(),
        "timeout": config.timeout_seconds,
        "verify": True,
        "enable_pii_log": False,
        "app_name": "curso-graph",
        "app_version": "4.0",
    }
    try:
        if modo == "apponly":
            secreto = os.getenv("CLIENT_SECRET", "")
            if not secreto.strip():
                raise RuntimeError("CLIENT_SECRET no puede estar vacío.")
            return msal.ConfidentialClientApplication(
                client_id, client_credential=secreto, **opciones
            )
        return msal.PublicClientApplication(client_id, **opciones)
    except ValueError:
        raise RuntimeError("No se pudo inicializar MSAL; revisa la autoridad.") from None


def invocar_msal(operacion, run_id):
    for intento in (1, 2):
        try:
            return operacion()
        except requests.exceptions.SSLError:
            raise ErrorAutenticacion("tls_auth: revisa certificados y proxy.") from None
        except (requests.Timeout, requests.ConnectionError) as error:
            LOG.warning(
                "evento=auth_red run_id=%s intento=%s tipo=%s",
                run_id, intento, type(error).__name__
            )
            if intento == 2:
                raise ErrorAutenticacion("red_auth: se agotaron los intentos.") from None
            time.sleep(1)


def registrar_resultado(resultado, metodo, run_id, historial, inicio):
    resultado = resultado if isinstance(resultado, dict) else {}
    token = resultado.get("access_token")
    correcto = isinstance(token, str) and bool(token)
    origen = resultado.get("token_source")
    if origen not in {"cache", "identity_provider", "broker"}:
        origen = "no_informado"
    codigos = resultado.get("error_codes")
    codigos = [x for x in codigos if type(x) is int] if isinstance(codigos, list) else []
    registro = {
        "metodo": metodo,
        "resultado": "token_obtenido" if correcto else "error",
        "origen": origen,
        "error": None if correcto else codigo_seguro(resultado.get("error")),
        "error_codes": codigos,
        "correlation_id": identificador_seguro(resultado.get("correlation_id")),
        "duracion_ms": round((time.perf_counter() - inicio) * 1000, 2),
    }
    historial.append(registro)
    LOG.info(
        "evento=auth run_id=%s metodo=%s resultado=%s origen=%s "
        "correlation_id=%s duracion_ms=%s",
        run_id, metodo, registro["resultado"], origen,
        registro["correlation_id"], registro["duracion_ms"]
    )
    return registro


def exigir_token(resultado, registro):
    if registro["resultado"] != "token_obtenido":
        raise ErrorAutenticacion(
            f"auth_rechazada: {registro['error']}; códigos={registro['error_codes']}"
        )
    return resultado["access_token"]


def obtener_token(cliente, modo, run_id, historial, permitir_interaccion=True):
    inicio = time.perf_counter()
    if modo == "apponly":
        resultado = invocar_msal(
            lambda: cliente.acquire_token_for_client(scopes=SCOPES_APLICACION),
            run_id,
        )
        registro = registrar_resultado(
            resultado, "client_credentials", run_id, historial, inicio
        )
        return exigir_token(resultado, registro)

    cuentas = cliente.get_accounts()
    if len(cuentas) > 1:
        raise ErrorAutenticacion("seleccion_cuenta_requerida: hay varias cuentas.")
    if cuentas:
        resultado = invocar_msal(
            lambda: cliente.acquire_token_silent_with_error(
                scopes=SCOPES_DELEGADOS, account=cuentas[0]
            ),
            run_id,
        )
        if resultado is not None:
            registro = registrar_resultado(
                resultado, "silent", run_id, historial, inicio
            )
            if registro["resultado"] == "token_obtenido":
                return exigir_token(resultado, registro)
            if registro["error"] not in ERRORES_INTERACTIVOS:
                return exigir_token(resultado, registro)

    if not permitir_interaccion:
        raise ErrorAutenticacion("interaccion_requerida: no hay token silencioso.")
    inicio = time.perf_counter()
    flujo = cliente.initiate_device_flow(scopes=SCOPES_DELEGADOS)
    if not isinstance(flujo, dict) or not flujo.get("user_code") or not flujo.get("message"):
        registro = registrar_resultado(
            flujo, "device_inicio", run_id, historial, inicio
        )
        raise ErrorAutenticacion(f"device_no_iniciado: {registro['error']}")
    print(flujo["message"], flush=True)
    resultado = cliente.acquire_token_by_device_flow(flujo)
    registro = registrar_resultado(
        resultado, "device_code", run_id, historial, inicio
    )
    return exigir_token(resultado, registro)
