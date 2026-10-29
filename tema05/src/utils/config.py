import os
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    tenant_id: str
    client_id_delegated: str
    graph_api_url: str
    timeout_seconds: float
    log_level: str


def leer_config(validar_identidad: bool = True) -> Config:
    load_dotenv(ROOT / ".env", override=False)
    tenant_id = os.getenv("TENANT_ID", "").strip()
    client_id = os.getenv("CLIENT_ID_DELEGATED", "").strip()

    if validar_identidad:
        for nombre, valor in (
            ("TENANT_ID", tenant_id),
            ("CLIENT_ID_DELEGATED", client_id),
        ):
            try:
                identificador = UUID(valor)
            except ValueError:
                raise RuntimeError(f"{nombre} debe contener un UUID válido.") from None
            if identificador.int == 0:
                raise RuntimeError(f"{nombre} debe contener un identificador real.")

    graph_url = os.getenv(
        "GRAPH_API_URL", "https://graph.microsoft.com/v1.0"
    ).strip().rstrip("/")
    if graph_url != "https://graph.microsoft.com/v1.0":
        raise RuntimeError("GRAPH_API_URL debe ser https://graph.microsoft.com/v1.0.")

    try:
        timeout = float(os.getenv("HTTP_TIMEOUT", "15"))
    except ValueError:
        raise RuntimeError("HTTP_TIMEOUT debe ser un número positivo.") from None
    if not isfinite(timeout) or timeout <= 0:
        raise RuntimeError("HTTP_TIMEOUT debe ser un número positivo y finito.")

    nivel = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    if nivel not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise RuntimeError("LOG_LEVEL no es válido.")

    return Config(tenant_id, client_id, graph_url, timeout, nivel)
