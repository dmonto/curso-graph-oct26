import json
from contextlib import contextmanager
from uuid import uuid4
from src.utils.config import leer_config
from src.utils.auth_msal import crear_cliente, obtener_token
from src.utils.graph_client import ClienteGraph

@contextmanager
def conectar():
    config = leer_config(validar_identidad=False)
    cliente = crear_cliente(config, "apponly")
    run_id, historial = str(uuid4()), []
    def proveedor():
        return obtener_token(cliente, "apponly", run_id, historial, False)
    with ClienteGraph(config, proveedor) as graph:
        yield graph

def mostrar(datos):
    print(json.dumps(datos, ensure_ascii=False, indent=2))

def ejecutar(main):
    try:
        return main() or 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"Error: {type(error).__name__}. Revisa la configuración, los permisos y los argumentos.")
        return 1
