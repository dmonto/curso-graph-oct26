from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
from html import escape
from datetime import datetime, timedelta, timezone
def obtener_tareas_completadas(graph):
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    tasks = graph.items("/planner/plans/" + segment(required("PLAN_ID")) + "/tasks")
    return [t for t in tasks if t.get("percentComplete") == 100
            and t.get("completedDateTime") and utc_date(t["completedDateTime"]) >= cutoff]
def obtener_archivos_recientes(graph):
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    path = "/sites/" + segment(required("SITE_ID")) + "/drive/root:/CursoGraph:/children"
    items = graph.items(path)
    return sorted([x for x in items if "file" in x and
                   utc_date(x["lastModifiedDateTime"]) >= cutoff],
                  key=lambda x: x["lastModifiedDateTime"], reverse=True)
def obtener_correos_relevantes(graph):
    keyword = os.getenv("ASUNTO_CLAVE", "Proyecto X").casefold()
    messages = graph.items("/me/mailFolders/inbox/messages", params={
        "$select": "id,subject,from,receivedDateTime,bodyPreview",
        "$orderby": "receivedDateTime desc", "$top": 100})
    return [m for m in messages if keyword in (m.get("subject") or "").casefold()][:5]
def generar_html(tasks, files, messages):
    def listing(rows, field):
        return "<ul>" + "".join("<li>" + escape(str(x.get(field, ""))) + "</li>" for x in rows) + "</ul>"
    return ("<h2>Reporte semanal</h2><h3>Tareas completadas</h3>" + listing(tasks, "title") +
            "<h3>Archivos modificados</h3>" + listing(files, "name") +
            "<h3>Correos relevantes</h3>" + listing(messages, "subject"))

from graph_client import Graph
from config import required
from util import run, show, output, segment, utc_date

def main(args):
    graph = Graph(["Tasks.Read","Files.Read","Mail.Read","Mail.Send"], args.device_code)
    try:
        tasks = obtener_tareas_completadas(graph)
        files = obtener_archivos_recientes(graph)
        messages = obtener_correos_relevantes(graph)
        html = generar_html(tasks, files, messages)
        output(__file__, "reporte.html", html)
        graph.call("POST", "/me/sendMail", expected=(202,), json={"message": {
            "subject": "Reporte semanal - Curso Graph", "body": {"contentType": "HTML", "content": html},
            "toRecipients": [{"emailAddress": {"address": required("TEST_RECIPIENT_UPN")}}]},
            "saveToSentItems": True})
        print("Graph aceptó el envío (202); no confirma la entrega.")
    finally:
        graph.close()

if __name__ == "__main__":
    run(main)
