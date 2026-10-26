from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
def obtener_correos_relevantes(graph):
    keyword = os.getenv("ASUNTO_CLAVE", "Proyecto X").casefold()
    messages = graph.items("/me/mailFolders/inbox/messages", params={
        "$select": "id,subject,from,receivedDateTime,bodyPreview",
        "$orderby": "receivedDateTime desc", "$top": 100})
    return [m for m in messages if keyword in (m.get("subject") or "").casefold()][:5]

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Mail.Read"], args.device_code)
    try:
        show(obtener_correos_relevantes(graph))
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
