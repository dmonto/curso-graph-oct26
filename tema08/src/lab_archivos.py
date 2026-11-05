import hashlib
import re
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote

from src.utils.files_client import ClienteArchivos, ruta_item, segmento
from src.utils.graph_client import ErrorGraph

DRIVE_DEMO = "DRIVE-DEMO"
CARPETA_DEMO = "CARPETA-DEMO"
ARCHIVO_DEMO = "ARCHIVO-DEMO"


class ArchivosLocales(ClienteArchivos):
    """Simulación en memoria: cada proceso empieza con los mismos datos ficticios."""
    def __init__(self, parcial=False):
        super().__init__(SimpleNamespace(graph_api_url="https://graph.microsoft.com/v1.0",
                                        timeout_seconds=15), lambda: "no-usado")
        self.parcial = parcial
        self.items = {
            CARPETA_DEMO: self._item(CARPETA_DEMO, "CURSO-Automatizaciones", None, carpeta=True),
            ARCHIVO_DEMO: self._item(ARCHIVO_DEMO, "resumen-proveedores.csv", CARPETA_DEMO),
            "ITEM-RRHH": self._item("ITEM-RRHH", "rrhh-agregado.csv", CARPETA_DEMO),
            "ITEM-CENTROS": self._item("ITEM-CENTROS", "centros.csv", CARPETA_DEMO),
        }
        self.contenidos = {ARCHIVO_DEMO: b"categoria;pendientes\nproveedores;3\n"}
        self.items[ARCHIVO_DEMO]["size"] = len(self.contenidos[ARCHIVO_DEMO])
        self.permisos = [{"id": "PERM-BASE", "roles": ["write"],
                          "inheritedFrom": {"id": "RAIZ-DEMO"}},
                         {"id": "PERM-ANONIMO-DEMO", "roles": ["read"],
                          "link": {"type": "view", "scope": "anonymous"}}]
        self.sesiones = {}

    @staticmethod
    def _item(item_id, nombre, parent, carpeta=False, contenido=b""):
        return {"id": item_id, "name": nombre, "eTag": f'"{item_id},1"',
                "size": len(contenido), "folder" if carpeta else "file": {},
                "parentReference": {"driveId": DRIVE_DEMO, "id": parent},
                "webUrl": "https://contoso.sharepoint.com/sites/Curso/Documentos/" + segmento(nombre)}

    def peticion(self, metodo, ruta, params=None, cuerpo=None, headers=None):
        if metodo != "GET":
            raise ValueError("La simulación usa escribir para las mutaciones.")
        if ruta.startswith("/teams/") and ruta.endswith("/filesFolder"):
            return deepcopy(self.items[CARPETA_DEMO])
        item_id = unquote(ruta.split("/items/", 1)[1])
        if item_id not in self.items:
            raise ErrorGraph("itemNotFound", 404)
        return deepcopy(self.items[item_id])

    def listar(self, ruta, params=None, headers=None, max_paginas=100):
        if max_paginas < 1:
            raise ValueError("max_paginas debe ser positivo.")
        base, operacion = ruta.rsplit("/", 1)
        item_id = unquote(base.split("/items/", 1)[1])
        if item_id not in self.items:
            return {"elementos": [], "paginas": 0, "completo": False,
                    "error": ErrorGraph("itemNotFound", 404).como_dict()}
        if operacion == "children":
            filas = [x for x in self.items.values() if x["parentReference"]["id"] == item_id]
        elif operacion == "permissions":
            filas = self.permisos
        elif operacion == "versions":
            filas = [{"id": "2.0", "size": 36}, {"id": "1.0", "size": 30}]
        elif operacion.startswith("search("):
            consulta = unquote(operacion.split("q='", 1)[1][:-2]).replace("''", "'")
            filas = [x for x in self.items.values() if consulta.casefold() in x["name"].casefold()]
        else:
            raise ValueError("Consulta local no implementada.")
        parcial = self.parcial or (operacion == "children" and len(filas) > 2 and max_paginas == 1)
        error = ErrorGraph("reintento_aplazado" if self.parcial else "limite_paginas", 429)
        return {"elementos": deepcopy(filas[:2] if parcial else filas),
                "paginas": 1 if parcial or len(filas) <= 2 else 2,
                "completo": not parcial, "error": error.como_dict() if parcial else None}

    def escribir(self, metodo, ruta, cuerpo=None, datos=None, params=None,
                 headers=None, esperados=(200, 201)):
        self.historial.append({"metodo": metodo, "local": True, "ruta": ruta})
        if ruta.endswith("/createLink"):
            return {"id": "PERM-CREADO-DEMO", "roles": ["read"], "link": {
                "type": cuerpo["type"], "scope": cuerpo["scope"]},
                "expirationDateTime": cuerpo.get("expirationDateTime")}
        if metodo == "PATCH":
            item_id = unquote(ruta.split("/items/", 1)[1])
            item = self.items[item_id]
            if (headers or {}).get("If-Match") != item["eTag"]:
                raise ErrorGraph("preconditionFailed", 412)
            item.update(cuerpo)
            item["eTag"] = f'"{item_id},2"'
            return deepcopy(item)
        if ruta.endswith("/children"):
            parent = unquote(ruta.split("/items/", 1)[1].rsplit("/", 1)[0])
            nombre = cuerpo["name"]
            carpeta = True
        else:
            parent, final = ruta.split("/items/", 1)[1].split(":/", 1)
            parent, nombre = unquote(parent), unquote(final.split(":/", 1)[0])
            carpeta = False
        if any(x["name"] == nombre and x["parentReference"]["id"] == parent
               for x in self.items.values()):
            raise ErrorGraph("nameAlreadyExists", 409)
        if ruta.endswith("/createUploadSession"):
            url = "https://transferencia.example.invalid/" + str(len(self.sesiones) + 1)
            self.sesiones[url] = {"parent": parent, "name": nombre, "bytes": bytearray()}
            return {"uploadUrl": url, "expirationDateTime": "2099-01-01T00:00:00Z"}
        return self._guardar(parent, nombre, datos or b"", carpeta)

    def _guardar(self, parent, nombre, contenido, carpeta=False):
        if parent not in self.items or "folder" not in self.items[parent]:
            raise ErrorGraph("itemNotFound", 404)
        item_id = f"ITEM-NUEVO-{len(self.items)}"
        self.items[item_id] = self._item(item_id, nombre, parent, carpeta, contenido)
        self.contenidos[item_id] = bytes(contenido)
        return deepcopy(self.items[item_id])

    def transferir_json(self, metodo, url, datos=None, headers=None, esperados=(200,)):
        sesion = self.sesiones[url]
        inicio, fin, total = map(int, re.fullmatch(
            r"bytes (\d+)-(\d+)/(\d+)", headers["Content-Range"]).groups())
        if inicio != len(sesion["bytes"]) or fin - inicio + 1 != len(datos):
            raise ErrorGraph("invalidRange", 416)
        sesion["bytes"].extend(datos)
        self.historial.append({"operacion": "fragmento", "local": True,
                               "rango": headers["Content-Range"]})
        if fin + 1 == total:
            return 201, self._guardar(sesion["parent"], sesion["name"], sesion["bytes"])
        return 202, {"nextExpectedRanges": [f"{fin + 1}-"]}

    def descargar(self, drive_id, item_id, destino, limite=10 * 1024 * 1024):
        self.peticion("GET", ruta_item(drive_id, item_id))
        contenido = self.contenidos.get(item_id, b"")
        if len(contenido) > limite:
            raise ValueError("Descarga superior al límite local.")
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        return {"bytes": len(contenido), "sha256": hashlib.sha256(contenido).hexdigest(),
                "destino": str(destino)}
