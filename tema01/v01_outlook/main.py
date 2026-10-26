from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Mail.Read"], args.device_code)
    try:
        messages = graph.items("/me/mailFolders/inbox/messages", params={
            "$select": "id,subject,from,receivedDateTime,isRead",
            "$orderby": "receivedDateTime desc", "$top": 50})
        unread = [m for m in messages if not m.get("isRead")][:5]
        show(unread)
        print(f"Mostrados: {len(unread)}")
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
