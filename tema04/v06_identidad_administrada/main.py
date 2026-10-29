# Permite ejecutar desde esta carpeta o desde la raíz.
import sys
from pathlib import Path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

import msal
import requests

from src.utils.auth_msal import codigo_seguro


class SesionConTimeout(requests.Session):
    def request(self, *args, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = 15
        return super().request(*args, **kwargs)


def main():
    try:
        with SesionConTimeout() as sesion:
            cliente = msal.ManagedIdentityClient(
                msal.SystemAssignedManagedIdentity(), http_client=sesion
            )
            resultado = cliente.acquire_token_for_client(
                resource="https://graph.microsoft.com"
            )
            token = resultado.get("access_token")
            if not isinstance(token, str) or not token:
                print(f"Autenticación fallida: {codigo_seguro(resultado.get('error'))}")
                return 1
            respuesta = sesion.get(
                "https://graph.microsoft.com/v1.0/users",
                headers={"Authorization": f"Bearer {token}"},
                params={"$select": "id", "$top": "1"},
                allow_redirects=False,
            )
            print(f"Graph: HTTP {respuesta.status_code}")
            return 0 if respuesta.status_code == 200 else 1
    except requests.RequestException as error:
        print(f"Fallo de red: {type(error).__name__}")
        return 1
    except (RuntimeError, ValueError):
        print("Identidad administrada no disponible o respuesta inválida.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
