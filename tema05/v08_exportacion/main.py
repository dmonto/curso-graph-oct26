import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import csv
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import requests

from src.smoke_test import comprobar_dependencias, comprobar_entorno
from src.utils.auth_msal import crear_cliente, obtener_token
from src.utils.config import leer_config
from src.utils.graph_client import ClienteGraph, ErrorGraph

ROOT = Path(__file__).resolve().parents[1]
SALIDA = Path(__file__).resolve().parent
CAMPOS_USUARIO = "id,displayName,userPrincipalName,mail,department,accountEnabled,userType"
CAMPOS_GRUPO = "id,displayName,mail,groupTypes,securityEnabled,mailEnabled"
CAMPOS_RESPONSABLE = ["caso", "upn", "user_id", "group_id", "estado"]


def uuid_real(valor, nombre="Identificador"):
    try:
        identificador = UUID(valor)
    except (ValueError, TypeError, AttributeError):
        raise RuntimeError(f"{nombre} debe contener un UUID válido.") from None
    if identificador.int == 0:
        raise RuntimeError(f"{nombre} debe contener un UUID real.")
    return str(identificador)


def literal_odata(valor):
    return "'" + valor.replace("'", "''") + "'"


def resolver_usuario(graph, upn):
    resultado = graph.listar("/users", params={
        "$filter": f"userPrincipalName eq {literal_odata(upn)}",
        "$select": CAMPOS_USUARIO, "$top": "2",
    })
    if not resultado["completo"]:
        error = resultado["error"]
        raise ErrorGraph(error["codigo"], error["http_status"])
    usuarios = resultado["elementos"]
    if not usuarios:
        return None
    if len(usuarios) != 1:
        raise ErrorGraph("identidad_ambigua")
    return usuarios[0]


def leer_casos(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames != ["caso", "upn"]:
            raise RuntimeError("El CSV de entrada debe tener las columnas caso,upn.")
        casos = list(lector)
    if not casos or len(casos) > 100:
        raise RuntimeError("El CSV debe contener entre 1 y 100 casos.")
    if any(None in fila or any(valor is None for valor in fila.values()) for fila in casos):
        raise RuntimeError("El CSV contiene filas incompletas o columnas adicionales.")
    return casos


def preparar_responsables(graph, casos, grupo_id, miembros):
    ids = {x["id"] for x in miembros["elementos"]}
    resoluciones = {}
    filas = []
    for caso in casos:
        upn = caso["upn"].strip().casefold()
        fila = {"caso": caso["caso"].strip(), "upn": upn, "user_id": "",
                "group_id": grupo_id, "estado": "entrada_invalida"}
        filas.append(fila)
        if not fila["caso"] or not upn:
            continue
        try:
            if upn not in resoluciones:
                resoluciones[upn] = resolver_usuario(graph, upn)
            usuario = resoluciones[upn]
            if usuario is None:
                fila["estado"] = "no_encontrado"
                continue
            fila["user_id"] = usuario["id"]
            if usuario.get("accountEnabled") is not True:
                fila["estado"] = "cuenta_no_habilitada_o_no_verificada"
            elif usuario.get("userType") != "Member":
                fila["estado"] = "tipo_usuario_requiere_revision"
            elif usuario["id"] in ids:
                fila["estado"] = "listo"
            elif miembros["completo"]:
                fila["estado"] = "pendiente_alta"
            else:
                fila["estado"] = "pertenencia_no_verificada"
        except ErrorGraph as error:
            if error.status == 401 or error.codigo == "autenticacion_fallida":
                raise
            fila["estado"] = f"error_{error.codigo}"
    return filas


def celda_segura(valor):
    if valor is None:
        return ""
    if isinstance(valor, (list, dict)):
        texto = json.dumps(valor, ensure_ascii=False)
    else:
        texto = str(valor)
    if texto.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + texto
    return texto


def escribir_csv(ruta, filas, campos):
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({campo: celda_segura(fila.get(campo)) for campo in campos})


def guardar_resultados(carpeta, informe):
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, campos in (("usuarios", CAMPOS_USUARIO.split(",")),
                           ("grupos", CAMPOS_GRUPO.split(",")),
                           ("miembros", ["id", "@odata.type", "displayName", "userPrincipalName"])):
        datos = informe["colecciones"].get(nombre)
        if datos is not None:
            escribir_csv(carpeta / f"{nombre}.csv", datos["elementos"], campos)
    escribir_csv(carpeta / "responsables.csv", informe["responsables"], CAMPOS_RESPONSABLE)
    (carpeta / "auditoria.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description="Auditoría de usuarios y grupos.")
    parser.add_argument("--entrada", default="datos/casos_tema5.csv")
    parser.add_argument("--grupo-id")
    parser.add_argument("--departamento")
    parser.add_argument("--tamano-pagina", type=int, choices=range(1, 100), default=25)
    parser.add_argument("--max-paginas", type=int, choices=range(1, 1001), default=100)
    args = parser.parse_args()
    informe = {"run_id": str(uuid4()), "fecha_utc": datetime.now(timezone.utc).isoformat(),
               "resultado": "error", "error": None, "auth": [], "http": [],
               "colecciones": {}, "responsables": [],
               "filtros": {"departamento": args.departamento}, "group_id": None}
    salida = 1
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        comprobar_entorno()
        comprobar_dependencias()
        config = leer_config(validar_identidad=False)
        logging.getLogger().setLevel(config.log_level)
        for nombre in ("msal", "urllib3", "requests"):
            logging.getLogger(nombre).setLevel(logging.WARNING)
        grupo_id = uuid_real(
            args.grupo_id or os.getenv("GROUP_ID", "").strip(), "GROUP_ID"
        )
        informe["group_id"] = grupo_id
        casos = leer_casos(ROOT / args.entrada)
        cliente = crear_cliente(config, "apponly")

        def proveedor():
            return obtener_token(cliente, "apponly", informe["run_id"], informe["auth"], False)

        with ClienteGraph(config, proveedor) as graph:
            informe["http"] = graph.historial
            parametros = {"$select": CAMPOS_USUARIO, "$top": str(args.tamano_pagina)}
            if args.departamento:
                parametros["$filter"] = f"department eq {literal_odata(args.departamento)}"
            informe["colecciones"]["usuarios"] = graph.listar(
                "/users", params=parametros, max_paginas=args.max_paginas
            )
            detener_si_fallo_identidad(informe["colecciones"]["usuarios"])
            informe["colecciones"]["grupos"] = graph.listar(
                "/groups", params={"$select": CAMPOS_GRUPO, "$top": str(args.tamano_pagina)},
                max_paginas=args.max_paginas,
            )
            detener_si_fallo_identidad(informe["colecciones"]["grupos"])
            miembros = graph.listar(f"/groups/{grupo_id}/members", max_paginas=args.max_paginas)
            informe["colecciones"]["miembros"] = miembros
            detener_si_fallo_identidad(miembros)
            informe["responsables"] = preparar_responsables(graph, casos, grupo_id, miembros)
        lecturas_ok = all(x["completo"] for x in informe["colecciones"].values())
        responsables_ok = all(x["estado"] == "listo" for x in informe["responsables"])
        informe["resultado"] = "ok" if lecturas_ok and responsables_ok else "parcial"
        salida = 0 if informe["resultado"] == "ok" else 2
    except KeyboardInterrupt:
        informe["error"] = "ejecucion_cancelada"
        salida = 130
    except ErrorGraph as error:
        informe["error"] = error.como_dict()
    except requests.RequestException as error:
        informe["error"] = f"red_auth_{type(error).__name__}"
    except (RuntimeError, ValueError):
        informe["error"] = "configuracion_o_autenticacion_invalida"
    except OSError:
        informe["error"] = "archivo_no_disponible"
    informe["exit_code"] = salida
    carpeta = SALIDA / "resultados" / f"tema5_{informe['run_id']}"
    try:
        guardar_resultados(carpeta, informe)
    except OSError:
        print("No se pudo guardar la auditoría.")
        return 1
    print(f"Resultado: {informe['resultado']}; exit_code={salida}; carpeta={carpeta}")
    return salida


def detener_si_fallo_identidad(coleccion):
    error = coleccion["error"]
    if error and (error["http_status"] == 401 or error["codigo"] == "autenticacion_fallida"):
        raise ErrorGraph(error["codigo"], error["http_status"])


if __name__ == "__main__":
    raise SystemExit(main())
