from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta, timezone
def obtener_tareas_completadas(graph):
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    tasks = graph.items("/planner/plans/" + segment(required("PLAN_ID")) + "/tasks")
    return [t for t in tasks if t.get("percentComplete") == 100
            and t.get("completedDateTime") and utc_date(t["completedDateTime"]) >= cutoff]

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Tasks.Read"], args.device_code)
    try:
        show(obtener_tareas_completadas(graph))
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
