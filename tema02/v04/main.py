from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.utils.config import leer_config
c=leer_config(validar_identidad=False)
print("Configuración local válida:", c.graph_api_url, c.timeout_seconds, c.log_level)
