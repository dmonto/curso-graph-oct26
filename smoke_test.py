import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import aiohttp  # Comprueba que la dependencia del temario está instalada.
import msal
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
SCOPES = [
    "User.Read", "User.Read.All", "Group.Read.All", "GroupMember.Read.All",
    "Mail.Read", "Mail.Send", "Calendars.ReadWrite", "Files.ReadWrite",
    "Tasks.ReadWrite", "ChannelMessage.Send",
]
RESULTS = []
ARTIFACTS = []


def config(name):
    value = os.getenv(name, "").strip()
    if not value or "{" in value or "}" in value:
        raise ValueError(f"Falta completar {name} en .env")
    return value


def check(name, operation):
    try:
        result = operation()
        RESULTS.append({"test": name, "status": "OK"})
        print(f"[OK] {name}")
        return result
    except Exception as exc:
        # Evitar que un secreto aparezca en un diagnóstico.
        detail = str(exc)
        secret = os.getenv("CLIENT_SECRET", "")
        if secret:
            detail = detail.replace(secret, "[OCULTO]")
        RESULTS.append({"test": name, "status": "ERROR", "detail": detail})
        print(f"[ERROR] {name}: {detail}")
        return None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def section(name, operation):
    try:
        operation()
    except Exception as exc:
        def failure():
            raise exc
        check(name, failure)


class Graph:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def call(self, method, path, expected=(200,), **kwargs):
        response = self.session.request(
            method, "https://graph.microsoft.com/v1.0" + path,
            timeout=(10, 30), allow_redirects=False, **kwargs,
        )
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = None
        if response.status_code not in expected:
            error = body.get("error", {}) if isinstance(body, dict) else {}
            request_id = response.headers.get("request-id", "no disponible")
            raise RuntimeError(
                f"HTTP {response.status_code}; {error.get('code', 'respuesta inesperada')}; "
                f"request-id={request_id}; Retry-After="
                f"{response.headers.get('Retry-After', 'no indicado')}"
            )
        require(isinstance(body, dict), "Respuesta JSON inesperada")
        require("error" not in body, "Graph ha devuelto un objeto de error")
        return body

    def item(self, path):
        body = self.call("GET", path)
        require(bool(body.get("id")), "La respuesta no contiene un id")
        return body

    def items(self, path):
        values = []
        while path:
            body = self.call("GET", path)
            require(isinstance(body.get("value"), list), "Falta la lista value")
            values.extend(body["value"])
            next_url = body.get("@odata.nextLink")
            prefix = "https://graph.microsoft.com/v1.0"
            require(not next_url or next_url.startswith(prefix + "/"),
                    "nextLink inesperado")
            path = next_url[len(prefix):] if next_url else None
        return values


def authenticate(mode, device_code):
    tenant = config("TENANT_ID")
    authority = f"https://login.microsoftonline.com/{tenant}"
    configured = os.getenv("AUTHORITY", authority).rstrip("/")
    require(configured == authority, "AUTHORITY no coincide con TENANT_ID")
    if mode == "DELEGATED":
        app = msal.PublicClientApplication(
            config("CLIENT_ID_DELEGATED"), authority=authority, timeout=30,
        )
        # MSAL añade openid, profile y offline_access automáticamente.
        scopes = [f"https://graph.microsoft.com/{scope}" for scope in SCOPES]
        if device_code:
            flow = app.initiate_device_flow(scopes=scopes)
            require("user_code" in flow, flow.get("error", "Device code no disponible"))
            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow)
        else:
            require(os.getenv("REDIRECT_URI", "http://localhost") == "http://localhost",
                    "La app pública debe tener REDIRECT_URI=http://localhost")
            result = app.acquire_token_interactive(
                scopes=scopes, prompt="select_account", timeout=180,
            )
    else:
        app = msal.ConfidentialClientApplication(
            config("CLIENT_ID_APPONLY"), authority=authority,
            client_credential=config("CLIENT_SECRET"), timeout=30,
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
    require("access_token" in result,
            f"{result.get('error', 'Sin token')}; correlation_id="
            f"{result.get('correlation_id', 'no disponible')}")
    return Graph(result["access_token"])


def validate_resources(graph, mode, me):
    names = ["GROUP_ID", "DRIVE_ID", "SITE_ID", "PLAN_ID", "BUCKET_ID"]
    names += ["TEAM_ID", "CHANNEL_ID"] if mode == "DELEGATED" else ["TEST_USER_UPN"]
    missing = [name for name in names if not os.getenv(name, "").strip()
               or "{" in os.getenv(name, "") or "}" in os.getenv(name, "")]
    require(not missing, "Completar en .env: " + ", ".join(missing))
    group = quote(config("GROUP_ID"), safe="")
    drive = quote(config("DRIVE_ID"), safe="")
    site = quote(config("SITE_ID"), safe="")
    plan = quote(config("PLAN_ID"), safe="")
    check(f"{mode}: usuarios", lambda: graph.items("/users?$top=1&$select=id"))
    check(f"{mode}: grupo", lambda: graph.item(f"/groups/{group}"))
    check(f"{mode}: miembros", lambda: graph.items(f"/groups/{group}/members?$select=id"))
    if me:
        check(f"{mode}: pertenencia al grupo",
              lambda: graph.item(f"/groups/{group}/members/{quote(me['id'], safe='')}"))

    def validate_drive():
        expected = config("DRIVE_ID")
        require(graph.item(f"/groups/{group}/drive")["id"] == expected,
                "DRIVE_ID no corresponde al grupo")
        require(graph.item(f"/sites/{site}/drive")["id"] == expected,
                "SITE_ID y DRIVE_ID no corresponden al mismo recurso")
        folder = graph.item(f"/drives/{drive}/root:/CursoGraph")
        require("folder" in folder, "/CursoGraph no es una carpeta")
    check(f"{mode}: SharePoint y carpeta /CursoGraph", validate_drive)

    def validate_plan():
        plans = graph.items(f"/groups/{group}/planner/plans")
        require(any(p.get("id") == config("PLAN_ID") for p in plans),
                "PLAN_ID no es un plan visible del grupo")
        buckets = graph.items(f"/planner/plans/{plan}/buckets")
        require(any(b.get("id") == config("BUCKET_ID") for b in buckets),
                "BUCKET_ID no pertenece al plan")
        graph.items(f"/planner/plans/{plan}/tasks")
    check(f"{mode}: Planner, buckets y tareas", validate_plan)
    mailbox = "/me" if mode == "DELEGATED" else "/users/" + quote(config("TEST_USER_UPN"), safe="")
    check(f"{mode}: correo", lambda: graph.items(
        mailbox + "/mailFolders/inbox/messages?$top=1&$select=id"))
    if mode == "DELEGATED":
        check("DELEGATED: OneDrive", lambda: graph.item("/me/drive"))
        check("DELEGATED: calendario", lambda: graph.items("/me/events?$top=1&$select=id"))
        team = quote(config("TEAM_ID"), safe="")
        channel = quote(config("CHANNEL_ID"), safe="")
        def validate_team():
            require(config("TEAM_ID") == config("GROUP_ID"),
                    "El Team del curso debe corresponder al grupo indicado")
            graph.item(f"/teams/{team}")
            graph.item(f"/teams/{team}/channels/{channel}")
            graph.items(f"/teams/{team}/channels/{channel}/messages?$top=1")
        check("DELEGATED: Team, canal y mensajes", validate_team)


def writes(graph, mode, tag):
    drive = quote(config("DRIVE_ID"), safe="")
    def file_test():
        item = graph.call("PUT", f"/drives/{drive}/root:/CursoGraph/{tag}-{mode}.txt:/content",
                          expected=(201,), data=b"Prueba CursoGraph",
                          headers={"Content-Type": "text/plain"})
        require(bool(item.get("id")), "Archivo sin id")
        ARTIFACTS.append({"type": "file", "mode": mode, "id": item["id"],
                          "drive_id": config("DRIVE_ID")})
        return item
    item = check(f"{mode}: subir archivo", file_test)
    if item:
        check(f"{mode}: enlace interno de lectura", lambda: graph.call(
            "POST", f"/drives/{drive}/items/{quote(item['id'], safe='')}/createLink",
            expected=(200, 201), json={"type": "view", "scope": "organization"}))

    def task_test():
        task = graph.call("POST", "/planner/tasks", expected=(201,), json={
            "planId": config("PLAN_ID"), "bucketId": config("BUCKET_ID"),
            "title": f"{tag} {mode}",
        })
        require(bool(task.get("id")), "Tarea sin id")
        ARTIFACTS.append({"type": "task", "mode": mode, "id": task["id"]})
        path = "/planner/tasks/" + quote(task["id"], safe="")
        current = graph.item(path)
        etag = current.get("@odata.etag")
        require(bool(etag), "Falta el ETag de la tarea")
        graph.call("PATCH", path, expected=(204,),
                   json={"percentComplete": 50}, headers={"If-Match": etag})
    check(f"{mode}: crear y actualizar tarea con ETag", task_test)

    if mode != "DELEGATED":
        return
    def event_test():
        start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=1)
        event = graph.call("POST", "/me/events", expected=(201,), json={
            "subject": tag,
            "start": {"dateTime": start.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"},
            "end": {"dateTime": (start + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"},
            "isReminderOn": False, "transactionId": str(uuid.uuid4()),
        })
        require(bool(event.get("id")), "Evento sin id")
        ARTIFACTS.append({"type": "event", "id": event["id"]})
        graph.call("PATCH", "/me/events/" + quote(event["id"], safe=""),
                   json={"subject": tag + " actualizado"})
    check("DELEGATED: crear y actualizar evento sin asistentes", event_test)
    check("DELEGATED: aceptar envío de correo", lambda: graph.call(
        "POST", "/me/sendMail", expected=(202,), json={"message": {
            "subject": tag, "body": {"contentType": "Text", "content": "Prueba de setup CursoGraph"},
            "toRecipients": [{"emailAddress": {"address": config("TEST_RECIPIENT_UPN")}}],
        }, "saveToSentItems": True}))
    team = quote(config("TEAM_ID"), safe="")
    channel = quote(config("CHANNEL_ID"), safe="")
    def message_test():
        message = graph.call("POST", f"/teams/{team}/channels/{channel}/messages",
                             expected=(201,), json={"body": {"contentType": "text", "content": tag}})
        require(bool(message.get("id")), "Mensaje sin id")
        ARTIFACTS.append({"type": "message", "id": message["id"],
                          "team_id": config("TEAM_ID"), "channel_id": config("CHANNEL_ID")})
    check("DELEGATED: publicar mensaje en Teams", message_test)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Ejecutar pruebas de escritura")
    parser.add_argument("--device-code", action="store_true", help="Autenticación por código de dispositivo")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        print("[ERROR] Se necesita Python 3.10 o superior")
        return 1
    load_dotenv(BASE_DIR / ".env", override=True)
    print(f"Python {sys.version.split()[0]} | aiohttp {aiohttp.__version__}")
    tag = "SMOKE-CursoGraph-" + uuid.uuid4().hex[:10]
    for mode in ("DELEGATED", "APP-ONLY"):
        graph = check(f"{mode}: autenticación", lambda: authenticate(mode, args.device_code))
        if graph is None:
            continue
        try:
            before = sum(r["status"] == "ERROR" for r in RESULTS)
            def identity():
                user = graph.item("/me")
                expected = config("USER_UPN")
                require(user.get("userPrincipalName", "").lower() == expected.lower(),
                        "Se ha iniciado sesión con otra cuenta; revisar USER_UPN")
                return user
            me = check("DELEGATED: /me y cuenta del alumno", identity) if mode == "DELEGATED" else None
            section(f"{mode}: configuración de recursos", lambda: validate_resources(graph, mode, me))
            if args.write:
                if sum(r["status"] == "ERROR" for r in RESULTS) == before:
                    section(f"{mode}: configuración de escritura", lambda: writes(graph, mode, tag))
                else:
                    RESULTS.append({"test": f"{mode}: escrituras", "status": "PENDIENTE"})
                    print(f"[PENDIENTE] {mode}: escrituras, resolver primero las lecturas")
        finally:
            graph.session.close()
    errors = sum(r["status"] == "ERROR" for r in RESULTS)
    report = {"date_utc": datetime.now(timezone.utc).isoformat(),
              "write_tests": args.write, "errors": errors,
              "tests": RESULTS, "created_resources": ARTIFACTS}
    output = BASE_DIR / "setup_resultados.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nInforme: {output.name}")
    if errors:
        print(f"[ERROR] {errors} comprobaciones fallidas. Revisar el informe.")
        return 1
    if not args.write:
        print("[PARCIAL] Lecturas correctas. Faltan las pruebas --write y las comprobaciones manuales.")
        return 2
    print("[OK] Pruebas automatizadas correctas. Completar la revisión manual del checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())