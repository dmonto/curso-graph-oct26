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

