import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import json
from uuid import uuid4

import requests

from src.directorio import uuid_real
from src.utils.auth_msal import crear_cliente, obtener_token
from src.utils.config import leer_config
from src.utils.graph_client import ClienteGraph, ErrorGraph


def cambiar_departamento(graph, usuario_id, departamento, aplicar=False):
    usuario_id = uuid_real(usuario_id)
    usuario = graph.peticion("GET", f"/users/{usuario_id}", params={
        "$select": "id,displayName,department,userType,onPremisesSyncEnabled"
    })
    if not usuario.get("displayName", "").upper().startswith("CURSO-"):
        raise RuntimeError("Utiliza una cuenta de prácticas con displayName CURSO-.")
    if usuario.get("onPremisesSyncEnabled") is True or usuario.get("userType") != "Member":
        raise RuntimeError("La práctica requiere un usuario interno administrado en la nube.")
    departamento = departamento.strip()
    if not departamento or len(departamento) > 64:
        raise RuntimeError("El departamento debe tener entre 1 y 64 caracteres.")
    resultado = {"accion": "actualizar_departamento", "user_id": usuario_id,
                 "antes": usuario.get("department"), "despues": departamento,
                 "estado": "simulado"}
    if usuario.get("department") == departamento:
        resultado["estado"] = "sin_cambio"
    elif aplicar:
        graph.peticion("PATCH", f"/users/{usuario_id}", cuerpo={"department": departamento})
        resultado["estado"] = "aceptado_204"
    return resultado


def cambiar_miembro(graph, grupo_id, usuario_id, accion, aplicar=False):
    if accion not in {"alta", "baja"}:
        raise ValueError("La acción debe ser alta o baja.")
    grupo_id, usuario_id = uuid_real(grupo_id), uuid_real(usuario_id)
    grupo = graph.peticion("GET", f"/groups/{grupo_id}", params={
        "$select": "id,displayName,groupTypes,securityEnabled,mailEnabled,"
                   "onPremisesSyncEnabled,isAssignableToRole"
    })
    tipos = grupo.get("groupTypes") or []
    compatible = "Unified" in tipos or (
        grupo.get("securityEnabled") is True and grupo.get("mailEnabled") is False
    )
    if (not grupo.get("displayName", "").upper().startswith("CURSO-")
        or not compatible or "DynamicMembership" in tipos
        or grupo.get("onPremisesSyncEnabled") is True
        or grupo.get("isAssignableToRole") is not False):
        raise RuntimeError("El grupo debe ser CURSO-, estático, cloud y sin asignación de roles.")
    usuario = graph.peticion("GET", f"/users/{usuario_id}", params={"$select": "id,displayName"})
    if not usuario.get("displayName", "").upper().startswith("CURSO-"):
        raise RuntimeError("Utiliza una cuenta de prácticas con displayName CURSO-.")
    miembros = graph.listar(f"/groups/{grupo_id}/members")
    if not miembros["completo"]:
        raise RuntimeError("La pertenencia no se pudo verificar completamente.")
    presente = usuario_id in {x["id"] for x in miembros["elementos"]}
    resultado = {"accion": accion, "group_id": grupo_id, "user_id": usuario_id,
                 "estado": "simulado"}
    if (accion == "alta" and presente) or (accion == "baja" and not presente):
        resultado["estado"] = "sin_cambio"
    elif aplicar:
        if accion == "alta":
            graph.peticion("POST", f"/groups/{grupo_id}/members/$ref", cuerpo={
                "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{usuario_id}"
            })
        else:
            graph.peticion("DELETE", f"/groups/{grupo_id}/members/{usuario_id}/$ref")
        resultado["estado"] = "aceptado_204"
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Cambios de prácticas; simulación por defecto.")
    parser.add_argument("--usuario-id", required=True)
    parser.add_argument("--aplicar", action="store_true")
    modos = parser.add_subparsers(dest="operacion", required=True)
    atributos = modos.add_parser("departamento")
    atributos.add_argument("--valor", required=True)
    miembros = modos.add_parser("miembro")
    miembros.add_argument("--grupo-id", required=True)
    miembros.add_argument("--accion", choices=("alta", "baja"), required=True)
    args = parser.parse_args()
    try:
        config = leer_config(validar_identidad=False)
        cliente = crear_cliente(config, "apponly")
        historial = []
        run_id = str(uuid4())

        def proveedor():
            return obtener_token(cliente, "apponly", run_id, historial, False)

        with ClienteGraph(config, proveedor) as graph:
            if args.operacion == "departamento":
                resultado = cambiar_departamento(graph, args.usuario_id, args.valor, args.aplicar)
            else:
                resultado = cambiar_miembro(
                    graph, args.grupo_id, args.usuario_id, args.accion, args.aplicar
                )
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0
    except ErrorGraph as error:
        print(json.dumps(error.como_dict(), ensure_ascii=False))
        return 1
    except requests.RequestException as error:
        print(f"Fallo de red de autenticación: {type(error).__name__}")
        return 1
    except (RuntimeError, ValueError):
        print("Revisa la identidad, los permisos y las condiciones de los objetos de prácticas.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
