import os
from urllib.parse import urlsplit
import requests
from auth import get_token
from config import required

class GraphError(RuntimeError):
    pass

class Graph:
    def __init__(self, scopes, device_code=False):
        base = os.getenv("GRAPH_API_URL", "https://graph.microsoft.com/v1.0").rstrip("/")
        if base != "https://graph.microsoft.com/v1.0":
            raise ValueError("Este paquete usa Microsoft Graph global v1.0")
        self.session = requests.Session()
        self.session.headers["Authorization"] = "Bearer " + get_token(scopes, device_code)
        me = self.call("GET", "/me", params={"$select": "id,userPrincipalName"})
        if me["userPrincipalName"].casefold() != required("USER_UPN").casefold():
            self.close()
            raise ValueError("La cuenta autenticada no coincide con USER_UPN")
        self.me = me

    def close(self):
        self.session.close()

    def call(self, method, path, version="v1.0", expected=(200,), **kwargs):
        if version not in ("v1.0", "beta"):
            raise ValueError("Version no permitida")
        url = path if path.startswith("https://") else f"https://graph.microsoft.com/{version}{path}"
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != "graph.microsoft.com"
                or not parsed.path.startswith(("/v1.0/", "/beta/"))):
            raise ValueError("URL Graph no permitida")
        response = self.session.request(method, url, timeout=(10, 30),
                                        allow_redirects=False, **kwargs)
        try:
            data = response.json() if response.content else {}
        except ValueError:
            raise GraphError(f"HTTP {response.status_code}: respuesta no JSON")
        if response.status_code not in expected:
            error = data.get("error", {}) if isinstance(data, dict) else {}
            raise GraphError(f"HTTP {response.status_code}: {error.get('code', 'error')}; "
                             f"request-id={response.headers.get('request-id')}; "
                             f"Retry-After={response.headers.get('Retry-After')}")
        return data

    def items(self, path, params=None, version="v1.0", limit=None, headers=None):
        result = []
        seen = set()
        while path:
            if path in seen:
                raise GraphError("Paginacion circular")
            seen.add(path)
            data = self.call("GET", path, version=version, params=params, headers=headers)
            if not isinstance(data, dict) or not isinstance(data.get("value"), list):
                raise GraphError("Falta la coleccion value")
            result.extend(data["value"])
            if limit is not None and len(result) >= limit:
                return result[:limit]
            path = data.get("@odata.nextLink")
            params = None
        return result
