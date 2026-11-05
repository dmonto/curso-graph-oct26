from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Cliente reutilizable: consulta local sin credenciales."""
from types import SimpleNamespace
from src.utils.teams_client import ClienteTeams
from src.teams_graph import BASE as GRAPH_BASE, EQUIPO_DEMO, SesionDemo
from src.ejemplos import guardar

def main():
    config = SimpleNamespace(graph_api_url=GRAPH_BASE, timeout_seconds=15)
    with ClienteTeams(config, lambda: "TOKEN_FICTICIO_SIN_VALIDEZ") as cliente:
        cliente.sesion.close()
        cliente.sesion = SesionDemo()
        datos = cliente.listar(f"/teams/{EQUIPO_DEMO}/channels")
        guardar(BASE / "resultados/canales.json", datos)
        guardar(BASE / "resultados/http.json", cliente.historial)
    print(f"Canales observados: {len(datos['elementos'])}; completo={datos['completo']}")
    return 0 if datos["completo"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
