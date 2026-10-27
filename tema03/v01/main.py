from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import leer_config
from src.validar_permisos import uuid_variable
leer_config()
print("Tenant y aplicación delegada: UUID válidos")
print("App-only:",uuid_variable("CLIENT_ID_APPONLY"))
print("La sintaxis de los IDs no acredita que existan en Entra.")
