from src.utils.files_client import ruta_item


def conceder_lectura(cliente, drive_id, item_id, correo_destinatario):
    return cliente.escribir("POST", ruta_item(drive_id, item_id) + "/invite", cuerpo={
        "recipients": [{"email": correo_destinatario}],
        "roles": ["read"], "requireSignIn": True,
        "sendInvitation": False, "retainInheritedPermissions": True,
    }, esperados=(200,))

from src.archivos_graph import permiso_visible
from src.utils.files_client import ruta_item, segmento


def cambiar_rol(cliente, drive_id, item_id, permiso, rol, etag):
    if rol not in {"read", "write"} or permiso.get("inheritedFrom"):
        raise ValueError("Rol o permiso no admitido en esta práctica.")
    if (permiso.get("link") or {}).get("scope") in {"organization", "users"}:
        raise ValueError("Este tipo de enlace no admite PATCH de roles.")
    ruta = ruta_item(drive_id, item_id) + "/permissions/" + segmento(permiso["id"])
    actualizado = cliente.escribir("PATCH", ruta, cuerpo={"roles": [rol]},
        headers={"If-Match": etag}, esperados=(200,))
    return permiso_visible(actualizado)


def revocar_permiso_creado(cliente, drive_id, item_id, permission_id, ids_creados, etag):
    if permission_id not in ids_creados:
        raise ValueError("El permiso no figura entre los creados por esta ejecución.")
    ruta = ruta_item(drive_id, item_id) + "/permissions/" + segmento(permission_id)
    cliente.escribir("DELETE", ruta, headers={"If-Match": etag}, esperados=(204,))
