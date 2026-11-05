import csv
import json
from uuid import UUID
from src.utils.graph_client import ErrorGraph

def uuid_real(valor, nombre="Identificador"):
    try:
        identificador = UUID(valor)
    except (ValueError, TypeError, AttributeError):
        raise RuntimeError(f"{nombre} debe contener un UUID válido.") from None
    if identificador.int == 0:
        raise RuntimeError(f"{nombre} debe contener un UUID real.")
    return str(identificador)


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


def detener_si_fallo_identidad(coleccion):
    error = coleccion.get("error") or {}
    if error.get("http_status") == 401 or error.get("codigo") == "autenticacion_fallida":
        raise ErrorGraph(error.get("codigo"), error.get("http_status"))
