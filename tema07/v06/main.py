from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from urllib.parse import quote
from src.auditar_directorio import uuid_real

def alta_miembro(usuario_id):
    usuario_id = uuid_real(usuario_id)
    return {
        "@odata.type": "#microsoft.graph.aadUserConversationMember",
        "roles": [],
        "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{usuario_id}')",
    }

def ruta_pertenencia(equipo_id, membership_id):
    return f"/teams/{uuid_real(equipo_id)}/members/{quote(membership_id, safe='')}"

def cambio_rol(propietario):
    return {"roles": ["owner"] if propietario else []}

from src.ejemplos import ejecutar_teams, guardar
from src.teams_graph import EQUIPO_DEMO

def main():
    codigo, informe = ejecutar_teams(BASE, ["--local", "miembros"])
    if codigo != 0:
        return codigo
    miembro = informe["datos"]["elementos"][1]
    propuesta = {
        "modo": "solo_propuestas_locales",
        "alta": {"metodo": "POST", "ruta": f"/teams/{EQUIPO_DEMO}/members",
                 "payload": alta_miembro(miembro["userId"])},
        "cambio_rol": {"metodo": "PATCH", "ruta": ruta_pertenencia(EQUIPO_DEMO, miembro["id"]),
                       "payload": cambio_rol(True)},
        "baja": {"metodo": "DELETE", "ruta": ruta_pertenencia(EQUIPO_DEMO, miembro["id"])},
        "user_id": miembro["userId"], "membership_id": miembro["id"],
    }
    guardar(BASE / "resultados/propuestas_miembros.json", propuesta)
    print("Propuestas guardadas. No se ha modificado ninguna pertenencia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
