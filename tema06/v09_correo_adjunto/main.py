from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import json
from src.outlook_acciones import adjunto_pequeno, leer_json
p = argparse.ArgumentParser()
p.add_argument("--archivo", required=True)
p.add_argument("--adjunto", default=str(ROOT / "datos/nota_tema6.txt"))
a = p.parse_args()
ruta = Path(a.archivo).resolve()
payload = leer_json(ruta)
payload["message"]["attachments"] = [adjunto_pequeno(Path(a.adjunto))]
destino = ruta.with_name("propuesta_correo_con_adjunto.json")
destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(destino)
