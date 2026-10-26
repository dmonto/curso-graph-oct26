from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta, timezone
def obtener_archivos_recientes(graph):
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    path = "/sites/" + segment(required("SITE_ID")) + "/drive/root:/CursoGraph:/children"
    items = graph.items(path)
    return sorted([x for x in items if "file" in x and
                   utc_date(x["lastModifiedDateTime"]) >= cutoff],
                  key=lambda x: x["lastModifiedDateTime"], reverse=True)

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Files.Read"], args.device_code)
    try:
        show(obtener_archivos_recientes(graph))
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
