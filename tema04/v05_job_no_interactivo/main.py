# Permite ejecutar desde esta carpeta o desde la raíz.
import sys
from pathlib import Path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import requests

from src.smoke_test import comprobar_dependencias, comprobar_entorno
from src.utils.auth_msal import (
    codigo_seguro, crear_cliente, identificador_seguro, obtener_token,
)
from src.utils.config import leer_config

ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger("curso_graph.demo")


class ErrorGraph(RuntimeError):
    pass


def consultar_graph(sesion, config, token, recurso, informe):
    client_request_id = str(uuid4())
    registro = {
        "client_request_id": client_request_id,
        "request_id": None,
        "http_status": None,
        "error": None,
        "elementos_validados": 0,
    }
    informe["graph"].append(registro)
    parametros = {"$select": "id"}
    if recurso == "users":
        parametros["$top"] = "1"
    inicio = time.perf_counter()
    try:
        respuesta = sesion.get(
            f"{config.graph_api_url}/{recurso}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "client-request-id": client_request_id,
                "return-client-request-id": "true",
            },
            params=parametros,
            timeout=config.timeout_seconds,
            allow_redirects=False,
        )
    except requests.RequestException as error:
        registro["error"] = f"red_graph_{type(error).__name__}"
        raise ErrorGraph(registro["error"]) from None
    finally:
        registro["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)

    registro["http_status"] = respuesta.status_code
    registro["request_id"] = identificador_seguro(respuesta.headers.get("request-id"))
    retry_after = respuesta.headers.get("Retry-After", "")
    if retry_after.isdecimal() and len(retry_after) <= 10:
        registro["retry_after_segundos"] = int(retry_after)
    LOG.info(
        "evento=graph run_id=%s client_request_id=%s request_id=%s "
        "http_status=%s duracion_ms=%s",
        informe["run_id"], client_request_id, registro["request_id"],
        registro["http_status"], registro["duracion_ms"]
    )
    try:
        datos = respuesta.json()
    except ValueError:
        datos = None
    if respuesta.status_code != 200:
        error_graph = datos.get("error") if isinstance(datos, dict) else None
        codigo = error_graph.get("code") if isinstance(error_graph, dict) else None
        registro["error"] = codigo_seguro(codigo)
        raise ErrorGraph(f"graph_rechazado: HTTP {respuesta.status_code}; {registro['error']}")
    if not isinstance(datos, dict):
        registro["error"] = "respuesta_json_invalida"
        raise ErrorGraph(registro["error"])
    if recurso == "me":
        if not isinstance(datos.get("id"), str) or not datos["id"]:
            registro["error"] = "perfil_sin_id"
            raise ErrorGraph(registro["error"])
        registro["elementos_validados"] = 1
    else:
        usuarios = datos.get("value")
        if not isinstance(usuarios, list) or any(
            not isinstance(x, dict) or not isinstance(x.get("id"), str) or not x["id"]
            for x in usuarios
        ):
            registro["error"] = "lista_usuarios_invalida"
            raise ErrorGraph(registro["error"])
        registro["elementos_validados"] = len(usuarios)


def main():
    parser = argparse.ArgumentParser(description="Autenticación MSAL y prueba de Graph.")
    parser.add_argument("--modo", choices=("delegada", "apponly"), default="apponly")
    parser.add_argument("--recurso", choices=("me", "users"))
    parser.add_argument("--repeticiones", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--sin-interaccion", action="store_true", default=True)
    parser.add_argument("--cache-cifrada", action="store_true")
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()
    recurso = args.recurso or ("me" if args.modo == "delegada" else "users")
    informe = {
        "run_id": str(uuid4()),
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "modo": args.modo,
        "recurso": recurso,
        "cache": "cifrada" if args.cache_cifrada else "memoria",
        "resultado": "error",
        "error": None,
        "auth": [],
        "graph": [],
    }
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    salida = 1
    try:
        comprobar_entorno()
        comprobar_dependencias()
        config = leer_config(validar_identidad=not args.local and args.modo == "delegada")
        logging.getLogger().setLevel(config.log_level)
        for nombre in ("msal", "urllib3", "requests"):
            logging.getLogger(nombre).setLevel(logging.WARNING)
        if args.local:
            informe["resultado"] = "local_ok"
        else:
            cache = None
            if args.cache_cifrada:
                from src.utils.cache_segura import crear_cache_cifrada
                cache = crear_cache_cifrada(args.modo)
            cliente = crear_cliente(config, args.modo, cache=cache)
            with requests.Session() as sesion:
                for _ in range(args.repeticiones):
                    token = obtener_token(
                        cliente, args.modo, informe["run_id"], informe["auth"],
                        permitir_interaccion=not args.sin_interaccion,
                    )
                    consultar_graph(sesion, config, token, recurso, informe)
            informe["resultado"] = "ok"
        salida = 0
    except KeyboardInterrupt:
        informe["error"] = "ejecucion_cancelada"
        salida = 130
    except requests.RequestException as error:
        informe["error"] = f"red_auth_{type(error).__name__}"
    except RuntimeError as error:
        informe["error"] = str(error)
    except ValueError:
        informe["error"] = "respuesta_o_configuracion_msal_invalida"
    informe["exit_code"] = salida
    if salida:
        LOG.error("evento=fin run_id=%s error=%s", informe["run_id"], informe["error"])
    try:
        carpeta = ROOT / "resultados"
        carpeta.mkdir(exist_ok=True)
        ruta = carpeta / f"msal_{args.modo}_{recurso}_{informe['run_id']}.json"
        ruta.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        LOG.error("evento=informe_no_guardado run_id=%s", informe["run_id"])
        return 1
    print(f"Resultado: {informe['resultado']}; exit_code={salida}; informe={ruta}")
    return salida


if __name__ == "__main__":
    raise SystemExit(main())
