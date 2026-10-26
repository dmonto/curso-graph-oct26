from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uuid

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Files.ReadWrite"], args.device_code)
    try:
        source = Path(__file__).parent / "reporte_local.txt"
        name = "CursoGraph-tema1-" + uuid.uuid4().hex[:8] + ".txt"
        result = graph.call("PUT", f"/me/drive/root:/{segment(name)}:/content",
            expected=(200, 201), data=source.read_bytes(), headers={"Content-Type": "text/plain"})
        show(result)
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
