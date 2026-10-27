from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import leer_config
c=leer_config()
print("Authority: https://login.microsoftonline.com/"+c.tenant_id)
print("Device code: app pública y flujo permitido; no usa redirect URI.")
print("Navegador interactivo: configurar http://localhost como app de escritorio.")
print("Comprobar single-tenant en el portal: no se deduce del UUID.")
