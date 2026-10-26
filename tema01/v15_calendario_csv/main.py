from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
import io
from datetime import datetime, timedelta, timezone

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Calendars.Read"], args.device_code)
    try:
        start = datetime.now(timezone.utc)
        events = graph.items("/me/calendarView", params={
            "startDateTime": start.isoformat(), "endDateTime": (start + timedelta(days=7)).isoformat(),
            "$select": "id,subject,start,end,importance,isAllDay", "$orderby": "start/dateTime"},
            headers={"Prefer": 'outlook.timezone="UTC"'})
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=["id", "asunto", "inicio_utc", "fin_utc", "minutos", "prioridad"])
        writer.writeheader()
        for event in events:
            a = datetime.fromisoformat(event["start"]["dateTime"]).replace(tzinfo=timezone.utc)
            b = datetime.fromisoformat(event["end"]["dateTime"]).replace(tzinfo=timezone.utc)
            writer.writerow({"id": event["id"], "asunto": event.get("subject", ""),
                "inicio_utc": a.isoformat(), "fin_utc": b.isoformat(),
                "minutos": (b-a).total_seconds()/60,
                "prioridad": "Alta" if event.get("importance") == "high" else "Normal"})
        output(__file__, "eventos.csv", buffer.getvalue())
        print(f"Eventos exportados: {len(events)}")
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
