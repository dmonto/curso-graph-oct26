import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from types import SimpleNamespace
from unittest.mock import Mock
from src.utils.graph_client import ClienteGraph
from src.runtime import mostrar, ejecutar

def main():
    p = argparse.ArgumentParser(description="Paginación interrumpida sin red")
    p.add_argument("--max-paginas", type=int, choices=[1,2], default=1)
    a = p.parse_args()
    config = SimpleNamespace(graph_api_url="https://graph.microsoft.com/v1.0", timeout_seconds=15)
    with ClienteGraph(config, lambda:"NO_USADO") as g:
        g.peticion = Mock(side_effect=[{"value":[{"id":"usuario-simulado-1"}], "@odata.nextLink":"https://graph.microsoft.com/v1.0/users?$skiptoken=demo"}, {"value":[{"id":"usuario-simulado-2"}]}])
        resultado = g.listar("/users", max_paginas=a.max_paginas)
        mostrar({"simulacion":True, **resultado})
        return 0 if resultado["completo"] else 2

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
