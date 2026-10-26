"""Diagnostico de lectura para CursoGraph. Python 3.10 o posterior.

Coloca este archivo junto al .env del curso y ejecuta:
    python diagnostico_graph.py
    python diagnostico_graph.py --only apponly

Dependencias: python -m pip install msal requests python-dotenv
Genera diagnostico_graph_resultados.json junto al script.
Solo lee Graph; los tokens y secretos se mantienen fuera del informe.
Los scopes predeterminados son User.Read y Group.Read.All, ya previstos
en el setup. Para probar otros scopes consentidos, usa --scopes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote
from uuid import UUID

try:
    import msal
    import requests
    from dotenv import dotenv_values, load_dotenv
except ImportError:
    raise SystemExit(
        "Instala las dependencias en el entorno del curso:\n"
        "python -m pip install msal requests python-dotenv"
    )

GRAPH = "https://graph.microsoft.com/v1.0"
ROOT = Path(__file__).resolve().parent


class Diagnostic:
    def __init__(self, config: dict[str, str], secrets: list[str] | None = None):
        self.config = config
        self.sensitive = [value for value in (secrets or []) if value]
        self.report = {
            "date_utc": datetime.now(timezone.utc).isoformat(),
            "write_tests": False,
            "warnings": [],
            "tests": [],
        }

    def clean(self, value):
        if isinstance(value, str):
            for sensitive in sorted(set(self.sensitive), key=len, reverse=True):
                value = value.replace(sensitive, "[REDACTADO]")
            return value
        if isinstance(value, dict):
            return {key: self.clean(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.clean(item) for item in value]
        return value

    def add(self, test, status, **details):
        row = self.clean({"test": test, "status": status, **details})
        self.report["tests"].append(row)
        print(json.dumps(row, indent=2, ensure_ascii=False))

    def warn(self, message):
        message = self.clean(message)
        self.report["warnings"].append(message)
        print("AVISO:", message)

    def require(self, *names):
        missing = [name for name in names if not self.config.get(name)]
        if missing:
            self.add("Configuracion", "ERROR", missing_variables=missing)
        return not missing

    def auth(self, mode):
        name = "CLIENT_ID_APPONLY" if mode == "apponly" else "CLIENT_ID_DELEGATED"
        required = ["TENANT_ID", name]
        if mode == "apponly":
            required.append("CLIENT_SECRET")
        if not self.require(*required):
            return None
        authority = "https://login.microsoftonline.com/" + self.config["TENANT_ID"]
        try:
            if mode == "apponly":
                app = msal.ConfidentialClientApplication(
                    self.config[name], authority=authority,
                    client_credential=self.config["CLIENT_SECRET"],
                )
                result = app.acquire_token_for_client(
                    scopes=["https://graph.microsoft.com/.default"]
                )
            else:
                scopes = self.config["scopes"]
                app = msal.PublicClientApplication(self.config[name], authority=authority)
                kwargs = {"scopes": scopes, "prompt": "select_account"}
                if self.config.get("TEST_USER_UPN"):
                    kwargs["login_hint"] = self.config["TEST_USER_UPN"]
                result = app.acquire_token_interactive(**kwargs)
        except Exception as exc:
            self.add(mode + ": autenticacion", "ERROR", exception=type(exc).__name__, detail=str(exc))
            return None
        if "access_token" not in result:
            # Lista permitida: nunca se guarda el resultado MSAL completo.
            details = {key: result[key] for key in (
                "error", "error_description", "error_codes", "suberror", "correlation_id"
            ) if key in result}
            self.add(mode + ": autenticacion", "ERROR", **details)
            return None
        token = result["access_token"]
        self.sensitive.append(token)
        self.add(mode + ": autenticacion", "OK", granted_scope=result.get("scope"))
        return token

    def get(self, session, token, test, path, **params):
        url = GRAPH + path
        try:
            response = session.get(
                url, params=params or None, timeout=(10, 30),
                headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
                allow_redirects=False,
            )
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            row = {"method": "GET", "endpoint": url, "params": params,
                   "http_status": response.status_code}
            if not 200 <= response.status_code < 300:
                error = payload.get("error", {}) if isinstance(payload, dict) else {}
                if not isinstance(error, dict):
                    error = {"message": str(error)}
                inner = error.get("innerError", error.get("innererror", {}))
                inner = inner if isinstance(inner, dict) else {}
                row.update(
                    graph_code=error.get("code"), graph_message=error.get("message"),
                    request_id=response.headers.get("request-id") or inner.get("request-id"),
                    retry_after=response.headers.get("Retry-After"),
                )
                self.add(test, "ERROR", **row)
                return None
            if isinstance(payload, dict) and isinstance(payload.get("value"), list):
                row["items_returned"] = len(payload["value"])
            if test == "delegated: /me" and isinstance(payload, dict):
                expected = self.config.get("TEST_USER_UPN")
                actual = payload.get("userPrincipalName", "")
                if expected:
                    row["matches_TEST_USER_UPN"] = actual.casefold() == expected.casefold()
                    if not row["matches_TEST_USER_UPN"]:
                        self.warn("La cuenta autenticada no coincide con TEST_USER_UPN.")
            self.add(test, "OK", **row)
            return payload
        except requests.RequestException as exc:
            self.add(test, "ERROR", endpoint=url, exception=type(exc).__name__, detail=str(exc))
            return None

    def run(self, mode="all"):
        with requests.Session() as session:
            if mode in ("all", "apponly"):
                token = self.auth("apponly")
                if token:
                    self.get(session, token, "apponly: usuarios", "/users", **{"$top": 1, "$select": "id"})
            if mode in ("all", "delegated"):
                token = self.auth("delegated")
                if token:
                    self.get(session, token, "delegated: /me", "/me", **{"$select": "userPrincipalName"})
                    if self.require("TEAM_ID", "CHANNEL_ID"):
                        team = quote(self.config["TEAM_ID"], safe="")
                        channel = quote(unquote(self.config["CHANNEL_ID"]), safe="")
                        team_path = "/teams/" + team
                        channel_path = team_path + "/channels/" + channel
                        # Cada llamada se registra por separado y sigue aunque otra falle.
                        self.get(session, token, "delegated: equipo", team_path)
                        self.get(session, token, "delegated: canal", channel_path)
                        self.get(session, token, "delegated: mensajes", channel_path + "/messages", **{"$top": 1})
        self.report["errors"] = sum(row["status"] == "ERROR" for row in self.report["tests"])
        return self.clean(self.report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--only", choices=["all", "delegated", "apponly"], default="all")
    parser.add_argument("--scopes", nargs="+", default=["User.Read", "Group.Read.All"])
    args = parser.parse_args(argv)
    env_path = args.env_file.expanduser().resolve()
    if not env_path.is_file():
        parser.error("No se encuentra el .env: " + str(env_path))
    file_values = dotenv_values(env_path, encoding="utf-8-sig", interpolate=False)
    keys = ["TENANT_ID", "AUTHORITY", "CLIENT_ID_DELEGATED", "CLIENT_ID_APPONLY",
            "CLIENT_SECRET", "TEAM_ID", "GROUP_ID", "CHANNEL_ID", "TEST_USER_UPN"]
    overrides = [key for key in keys if key in os.environ and key in file_values
                 and os.environ[key] != file_values[key]]
    # Conserva la precedencia habitual de load_dotenv y avisa de valores heredados.
    load_dotenv(env_path, override=False, encoding="utf-8-sig", interpolate=False)
    config = {key: os.getenv(key, "").strip() for key in keys}
    config["TEAM_ID"] = config["TEAM_ID"] or config["GROUP_ID"]
    config["scopes"] = [scope if scope.startswith("https://graph.microsoft.com/")
                        else "https://graph.microsoft.com/" + scope for scope in args.scopes]
    secrets = [os.getenv("CLIENT_SECRET", ""), file_values.get("CLIENT_SECRET") or ""]
    diag = Diagnostic(config, secrets)
    diag.report["requested_delegated_scopes"] = config["scopes"]
    if overrides:
        diag.warn("Variables del proceso prevalecen sobre el .env: " + ", ".join(overrides))
    expected_authority = "https://login.microsoftonline.com/" + config["TENANT_ID"]
    if config["AUTHORITY"] and config["AUTHORITY"].rstrip("/") != expected_authority:
        diag.warn("AUTHORITY difiere de TENANT_ID; este diagnostico deriva AUTHORITY de TENANT_ID.")
    if config["CLIENT_ID_APPONLY"] and config["CLIENT_ID_APPONLY"] == config["CLIENT_ID_DELEGATED"]:
        diag.warn("CLIENT_ID_APPONLY y CLIENT_ID_DELEGATED son iguales; el setup previsto usa dos apps.")
    if config["CLIENT_SECRET"]:
        try:
            UUID(config["CLIENT_SECRET"])
        except ValueError:
            pass
        else:
            diag.warn("CLIENT_SECRET tiene formato UUID; comprueba que has copiado Value y no Secret ID.")
    report = diag.run(args.only)
    output = ROOT / "diagnostico_graph_resultados.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Informe:", output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
