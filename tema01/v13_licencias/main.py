from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["User.Read.All"], args.device_code)
    try:
        licenses = graph.items("/me/licenseDetails")
        show(licenses)
        output(__file__, "licencias.json", json.dumps(licenses, ensure_ascii=False, indent=2))
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
