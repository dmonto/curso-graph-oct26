import os
import msal
from config import required

def get_token(scopes, device_code=False):
    authority = "https://login.microsoftonline.com/" + required("TENANT_ID")
    configured = os.getenv("AUTHORITY", "").strip().rstrip("/")
    if configured and configured != authority:
        raise ValueError("AUTHORITY no coincide con TENANT_ID")
    if os.getenv("REDIRECT_URI", "http://localhost") != "http://localhost":
        raise ValueError("Configura REDIRECT_URI=http://localhost")
    app = msal.PublicClientApplication(required("CLIENT_ID_DELEGATED"),
                                      authority=authority, timeout=30)
    scopes = ["https://graph.microsoft.com/" + s for s in sorted(set(scopes + ["User.Read"]))]
    if device_code:
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            raise RuntimeError("Device code no disponible: " + flow.get("error", "sin detalle"))
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
    else:
        result = app.acquire_token_interactive(scopes=scopes, prompt="select_account",
                                              login_hint=required("USER_UPN"), timeout=180)
    if "access_token" not in result:
        raise RuntimeError(f"Autenticacion: {result.get('error')}; correlation_id={result.get('correlation_id')}")
    return result["access_token"]
