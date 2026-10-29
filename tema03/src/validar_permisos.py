import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from src.smoke_test import (
    comprobar_dependencias,
    comprobar_entorno,
    obtener_token,
)

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("curso_graph.permisos")


def uuid_variable(nombre):
    valor = os.getenv(nombre, "").strip()
    try:
        identificador = UUID(valor)
    except ValueError:
        raise RuntimeError(f"{nombre} debe contener un UUID válido.") from None
    if identificador.int == 0:
        raise RuntimeError(f"{nombre} debe contener un identificador real.")
    return valor


def token_aplicacion(config):
    import msal
    import requests

    tenant_id = uuid_variable("TENANT_ID")
    client_id = uuid_variable("CLIENT_ID_APPONLY")
    secreto = os.getenv("CLIENT_SECRET", "")
    if not secreto.strip():
        raise RuntimeError("CLIENT_SECRET está vacío.")

    try:
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=secreto,
            timeout=config.timeout_seconds,
        )
        resultado = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
    except requests.RequestException:
        raise RuntimeError("Error de red al contactar con Entra ID.") from None
    except ValueError:
        raise RuntimeError("No se pudo validar la autoridad de la aplicación.") from None

    if "access_token" not in resultado:
        error = resultado.get("error", "sin_codigo")
        codigos = resultado.get("error_codes", [])
        correlacion = resultado.get("correlation_id", "no_disponible")
        raise RuntimeError(
            f"MSAL: {error}; códigos={codigos}; correlation_id={correlacion}."
        )
    logger.info("Token de aplicación recibido en memoria")
    print(resultado)
    return resultado["access_token"]


def probar_graph(config, token, recurso, informe):
    import requests

    parametros = {"$select": "id,displayName"}
    if recurso == "users":
        parametros["$top"] = 1

    try:
        with requests.Session() as session:
            respuesta = session.get(
                f"{config.graph_api_url}/{recurso}",
                headers={"Authorization": f"Bearer {token}"},
                params=parametros,
                timeout=config.timeout_seconds,
            )
            informe["http_status"] = respuesta.status_code
            informe["request_id"] = respuesta.headers.get("request-id")
            logger.info("GET /%s -> HTTP %s", recurso, respuesta.status_code)
            try:
                datos = respuesta.json()
            except ValueError:
                datos = None
    except requests.RequestException as error:
        raise RuntimeError(f"Error de red con Graph: {type(error).__name__}.") from None

    if respuesta.status_code != 200:
        detalle = datos.get("error", {}) if isinstance(datos, dict) else {}
        codigo = detalle.get("code", "sin_codigo") if isinstance(detalle, dict) else "sin_codigo"
        raise RuntimeError(f"Graph HTTP {respuesta.status_code}; error={codigo}.")
    if not isinstance(datos, dict):
        raise RuntimeError("Graph no devolvió un objeto JSON válido.")

    if recurso == "me":
        if not datos.get("id"):
            raise RuntimeError("La respuesta no contiene un perfil válido.")
        informe["registros_recibidos"] = 1
    else:
        usuarios = datos.get("value")
        if not isinstance(usuarios, list):
            raise RuntimeError("La respuesta no contiene una colección de usuarios.")
        informe["registros_recibidos"] = len(usuarios)


def main():
    parser = argparse.ArgumentParser(description="Validar permisos de las aplicaciones Graph")
    parser.add_argument("--modo", choices=["delegada", "apponly"], default="delegada")
    parser.add_argument("--recurso", choices=["me", "users"])
    args = parser.parse_args()
    recurso = args.recurso or ("me" if args.modo == "delegada" else "users")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    informe = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "modo": args.modo,
        "recurso": f"/{recurso}",
        "resultado": "ERROR",
        "http_status": None,
    }
    salida = 1

    try:
        comprobar_entorno()
        comprobar_dependencias()
        from src.utils.config import leer_config

        config = leer_config(validar_identidad=args.modo == "delegada")
        logger.setLevel(config.log_level)
        if args.modo == "delegada":
            token = obtener_token(config)
        else:
            token = token_aplicacion(config)
        probar_graph(config, token, recurso, informe)
        informe.update(resultado="OK", detalle="Consulta ejecutada y respuesta validada.")
        salida = 0
        logger.info("VALIDACIÓN OK | %s | /%s", args.modo, recurso)
    except KeyboardInterrupt:
        informe.update(resultado="INTERRUMPIDO", detalle="Interrupción de la ejecución.")
        salida = 130
    except (RuntimeError, ValueError, ImportError, OSError) as error:
        informe["detalle"] = str(error)
        logger.error("VALIDACIÓN ERROR | %s", error)

    informe["codigo_salida"] = salida
    try:
        carpeta = ROOT / "resultados"
        carpeta.mkdir(parents=True, exist_ok=True)
        archivo = carpeta / f"validacion_{args.modo}_{recurso}.json"
        archivo.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Informe guardado: %s", archivo.name)
    except OSError:
        logger.error("No se ha podido guardar el informe de validación")
        return 1
    return salida


if __name__ == "__main__":
    raise SystemExit(main())
