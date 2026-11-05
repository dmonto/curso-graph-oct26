from src.utils.files_client import ruta_item, segmento


def restaurar_version(cliente, drive_id, item_id, version_id):
    ruta = ruta_item(drive_id, item_id) + f"/versions/{segmento(version_id)}/restoreVersion"
    cliente.escribir("POST", ruta, esperados=(204,))
    return cliente.peticion("GET", ruta_item(drive_id, item_id))
