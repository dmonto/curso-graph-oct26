from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Tasks.ReadWrite"], args.device_code)
    try:
        result = graph.call("POST", "/planner/tasks", expected=(201,), json={
            "planId": required("PLAN_ID"), "bucketId": required("BUCKET_ID"),
            "title": "Implementar autenticación - Tema 1",
            "assignments": {graph.me["id"]: {
                "@odata.type": "#microsoft.graph.plannerAssignment", "orderHint": " !"}}})
        show(result)
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
