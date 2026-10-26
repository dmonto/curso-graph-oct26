from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import logging
from src.utils.config import leer_config
logging.basicConfig(level=logging.INFO,format="%(levelname)s | %(message)s")
try:
    c=leer_config(validar_identidad=False)
    logging.getLogger().setLevel(c.log_level)
    logging.info("Configuración correcta")
    logging.debug("Detalle de diagnóstico sin credenciales")
except (RuntimeError,ValueError) as exc:
    logging.error("%s",exc)
    raise SystemExit(1)
