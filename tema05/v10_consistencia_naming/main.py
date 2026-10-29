import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse, re
from src.runtime import conectar, mostrar, ejecutar
from src.directorio import CAMPOS_USUARIO

def evaluar(usuarios, grupos):
    incidencias = []
    permitidos = {"Financiero", "RRHH", "Mantenimiento"}
    for u in usuarios:
        d = u.get("department")
        if d not in permitidos:
            incidencias.append({"tipo":"departamento_fuera_convencion", "id":u["id"], "valor":d})
    for g in grupos:
        nombre = g.get("displayName", "")
        if not re.fullmatch(r"CURSO-GRAPH-(FIN|RRHH|MANT)-[A-Z0-9-]+", nombre):
            incidencias.append({"tipo":"nombre_grupo_fuera_convencion", "id":g["id"], "valor":nombre})
    return incidencias

def main():
    p = argparse.ArgumentParser(description="Revisión de naming, sin modificar directorio")
    p.add_argument("--demo", action="store_true", help="Datos ficticios sin red")
    a = p.parse_args()
    if a.demo:
        usuarios = {"elementos":[{"id":"demo-u1", "department":"FIN "}], "completo":True}
        grupos = {"elementos":[{"id":"demo-g1", "displayName":"CURSO-GRAPH-FIN-REVISORES"}], "completo":True}
    else:
        with conectar() as g:
            usuarios = g.listar("/users", params={"$select":CAMPOS_USUARIO})
            grupos = g.listar("/groups", params={"$select":"id,displayName"})
    incidencias = evaluar(usuarios["elementos"], grupos["elementos"])
    completo = usuarios["completo"] and grupos["completo"]
    mostrar({"simulacion":a.demo, "completo":completo, "incidencias":incidencias, "accion":"revisar_maestro_sin_cambios_automaticos"})
    return 0 if completo and not incidencias else 2

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
