from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Calendars.Read"], args.device_code)
    try:
        show(graph.items("/me/events", params={"$top": 5,
            "$select": "id,subject,start,end"}, limit=5))
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
