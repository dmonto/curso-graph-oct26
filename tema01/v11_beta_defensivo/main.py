from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Calendars.Read"], args.device_code)
    try:
        events = graph.items("/me/events", version="beta", params={"$top": 10}, limit=10)
        for event in events:
            if not isinstance(event, dict) or not isinstance(event.get("start"), dict):
                print("Evento omitido: estructura inesperada")
                continue
            show({"id": event.get("id"), "titulo": event.get("subject") or "Sin título",
                  "inicio": event["start"].get("dateTime"),
                  "importancia": event.get("importance", "no disponible")})
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
