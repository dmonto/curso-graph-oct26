from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["ChannelMessage.Send"], args.device_code)
    try:
        team, channel = segment(required("TEAM_ID")), segment(required("CHANNEL_ID"))
        result = graph.call("POST", f"/teams/{team}/channels/{channel}/messages",
            expected=(201,), json={"body": {"contentType": "html",
            "content": "<h3>Reporte diario</h3><p>Completado: <b>5 tareas</b>. Pendiente: 3.</p>"}})
        show(result)
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
