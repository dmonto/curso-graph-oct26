import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from src.runtime import conectar, mostrar, ejecutar
from src.directorio import literal_odata, CAMPOS_USUARIO

def main():
    p = argparse.ArgumentParser(description="Filtrado y paginación del directorio")
    p.add_argument("--departamento")
    p.add_argument("--tamano-pagina", type=int, choices=range(1,100), default=2)
    p.add_argument("--max-paginas", type=int, choices=range(1,1001), default=100)
    a = p.parse_args()
    parametros = {"$select":CAMPOS_USUARIO, "$top":str(a.tamano_pagina)}
    if a.departamento:
        parametros["$filter"] = f"department eq {literal_odata(a.departamento)}"
    with conectar() as g:
        resultado = g.listar("/users", params=parametros, max_paginas=a.max_paginas)
        mostrar(resultado)
        return 0 if resultado["completo"] else 2

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
