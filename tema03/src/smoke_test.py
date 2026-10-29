import argparse
import importlib
import logging
import sys
from importlib.metadata import version

logger = logging.getLogger("curso_graph.smoke")
PAQUETES = {
    "requests": "requests",
    "msal": "msal",
    "aiohttp": "aiohttp",
    "python-dotenv": "dotenv",
}


def comprobar_entorno():
    if sys.version_info < (3, 10):
        raise RuntimeError("Se requiere Python 3.10 o superior.")
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Utiliza el intérprete del entorno virtual.")
    logger.info("Python %s; entorno virtual OK", sys.version.split()[0])


def comprobar_dependencias():
    for paquete, modulo in PAQUETES.items():
        try:
            importlib.import_module(modulo)
            instalada = version(paquete)
        except ImportError:
            raise RuntimeError(
                f"No se puede cargar {paquete}. Revisa requirements.txt "
                "con python -m pip install -r requirements.txt."
            ) from None
        logger.info("Dependencia %s: %s", paquete, instalada)


def obtener_token(config):
    import msal
    import requests

    try:
        app = msal.PublicClientApplication(
            client_id=config.client_id_delegated,
            authority=f"https://login.microsoftonline.com/{config.tenant_id}",
            timeout=config.timeout_seconds,
        )
        flow = app.initiate_device_flow(
            scopes=["https://graph.microsoft.com/User.Read"]
        )
        if "user_code" not in flow:
            raise RuntimeError(
                f"MSAL no inició el flujo: {flow.get('error', 'sin_codigo')}."
            )
        print(flow["message"], flush=True)
        resultado = app.acquire_token_by_device_flow(flow)
        print(resultado)
    except requests.RequestException:
        raise RuntimeError("Error de red al contactar con Microsoft Entra ID.") from None
    except ValueError:
        raise RuntimeError("MSAL no pudo validar la autoridad. Revisa TENANT_ID.") from None

    if "access_token" not in resultado:
        raise RuntimeError(
            f"Autenticación fallida: {resultado.get('error', 'sin_codigo')}."
        )
    logger.info("Autenticación OK; token recibido en memoria")
    return resultado["access_token"]


def consultar_perfil(config, token):
    import requests

    try:
        with requests.Session() as session:
            respuesta = session.get(
                f"{config.graph_api_url}/me",
                headers={"Authorization": f"Bearer {token}"},
                params={"$select": "id,displayName,userPrincipalName,mail"},
                timeout=config.timeout_seconds,
            )
            logger.info("GET /me -> HTTP %s", respuesta.status_code)
            respuesta.raise_for_status()
            datos = respuesta.json()
    except requests.Timeout:
        raise RuntimeError("Tiempo de espera agotado al consultar Graph.") from None
    except requests.HTTPError as error:
        estado = error.response.status_code
        raise RuntimeError(f"Graph devolvió un error HTTP {estado}.") from None
    except ValueError:
        raise RuntimeError("Graph no devolvió un JSON válido.") from None
    except requests.RequestException:
        raise RuntimeError("Error de red al consultar Microsoft Graph.") from None

    if not isinstance(datos, dict) or not datos.get("id"):
        raise RuntimeError("La respuesta no contiene un perfil de usuario válido.")
    return datos


def main():
    parser = argparse.ArgumentParser(description="Comprobación del entorno Graph")
    parser.add_argument(
        "--local", action="store_true", help="Comprobar sin contactar con Entra ID ni Graph"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    try:
        comprobar_entorno()
        comprobar_dependencias()
        from src.utils.config import leer_config

        config = leer_config(validar_identidad=not args.local)
        logger.setLevel(config.log_level)
        logger.info("Configuración OK")

        if args.local:
            logger.info("SMOKE TEST LOCAL OK; Entra ID y Graph no comprobados")
            return 0

        token = obtener_token(config)
        perfil = consultar_perfil(config, token)
        logger.info("Perfil recibido y validado")
        logger.debug("Validación de identificador: %s", bool(perfil.get("id")))
        logger.info("SMOKE TEST COMPLETO OK")
        return 0
    except KeyboardInterrupt:
        logger.warning("Comprobación interrumpida")
        return 130
    except (RuntimeError, ValueError, ImportError, OSError) as error:
        logger.error("SMOKE TEST ERROR | %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
