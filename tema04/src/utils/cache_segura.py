from pathlib import Path

from src.utils.auth_msal import uuid_variable

ROOT = Path(__file__).resolve().parents[2]


def crear_cache_cifrada(modo):
    try:
        from msal_extensions import PersistedTokenCache, build_encrypted_persistence
    except ImportError:
        raise RuntimeError("Instala msal-extensions para usar --cache-cifrada.") from None

    tenant_id = uuid_variable("TENANT_ID")
    variable = "CLIENT_ID_APPONLY" if modo == "apponly" else "CLIENT_ID_DELEGATED"
    client_id = uuid_variable(variable)
    carpeta = ROOT / ".cache"
    carpeta.mkdir(mode=0o700, parents=True, exist_ok=True)
    ubicacion = carpeta / f"msal-{tenant_id}-{client_id}.bin"
    try:
        persistencia = build_encrypted_persistence(str(ubicacion))
        if not persistencia.is_encrypted:
            raise RuntimeError("La persistencia debe estar cifrada.")
        return PersistedTokenCache(persistencia)
    except Exception:
        raise RuntimeError(
            "Caché cifrada no disponible; revisa el servicio de cifrado del sistema."
        ) from None
