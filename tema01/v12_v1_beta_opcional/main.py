from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from graph_client import GraphError

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Calendars.Read"], args.device_code)
    try:
        events = graph.items("/me/events", params={"$top": 5, "$select": "id,subject,start,end"}, limit=5)
        for event in events:
            try:
                extra = graph.call("GET", "/me/events/" + segment(event["id"]),
                                   version="beta", params={"$select": "importance,categories"})
                event["datos_opcionales"] = extra
            except (GraphError, requests.RequestException) as exc:
                print(f"Se conserva el evento v1.0: {exc}")
        show(events)
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
