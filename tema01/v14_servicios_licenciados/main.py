from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["User.Read.All"], args.device_code)
    try:
        licenses = graph.items("/me/licenseDetails")
        for license in licenses:
            print("SKU:", license.get("skuPartNumber"))
            for plan in license.get("servicePlans", []):
                show({"servicio": plan.get("servicePlanName"), "id": plan.get("servicePlanId"),
                      "estado": plan.get("provisioningStatus")})
        print("Una licencia no garantiza permisos API, acceso a recursos ni ausencia de políticas.")
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
