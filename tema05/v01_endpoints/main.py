import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse, os
from src.runtime import conectar, mostrar, ejecutar
from src.directorio import uuid_real
from src.utils.config import leer_config

def main():
    p = argparse.ArgumentParser(description="Usuarios, grupos y pertenencias")
    p.add_argument("--recurso", choices=["users", "groups", "members", "transitiveMembers"], default="users")
    p.add_argument("--grupo-id")
    a = p.parse_args()
    gid = None
    if a.recurso not in ("users", "groups"):
        leer_config(validar_identidad=False)
        try:
            gid = uuid_real(
                a.grupo_id or os.getenv("GROUP_ID", ""),
                "--grupo-id o GROUP_ID",
            )
        except RuntimeError as error:
            p.error(str(error))
    with conectar() as g:
        ruta = "/" + a.recurso
        if a.recurso not in ("users", "groups"):
            ruta = f"/groups/{gid}/{a.recurso}"
        resultado = g.listar(ruta, params={"$select":"id,displayName"})
        mostrar(resultado)
        return 0 if resultado["completo"] else 2

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
