import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv
from src.outlook_lectura import informe_nuevo, correo_resumen, propuesta_cita

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
p = argparse.ArgumentParser(description="Genera propuestas locales sin llamar a Graph.")
p.add_argument("--dia", help="Fecha YYYY-MM-DD; por defecto mañana en UTC.")
a = p.parse_args()
dia = datetime.fromisoformat(a.dia).replace(tzinfo=timezone.utc) if a.dia else datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
informe = informe_nuevo(None, dia.isoformat(), (dia + timedelta(days=1)).isoformat())
informe["resultado"] = "ok"
informe["propuestas"] = [{"caso":"FIN-001", "titulo":"Revisar petición de proveedor", "estado":"pendiente_revision"}]
correo = correo_resumen(informe, os.getenv("COURSE_TEST_RECIPIENT") or "destinatario@ejemplo.invalid")
texto = json.loads(json.dumps(correo))
texto["message"]["body"] = {"contentType": "Text", "content": "Revisión de solicitudes pendientes. Caso FIN-001: revisar petición de proveedor."}
evento = propuesta_cita(informe)
actualizacion = {k:v for k,v in evento.items() if k != "transactionId"}
actualizacion["subject"] += " actualizada"
carpeta = ROOT / "resultados" / "payloads" / str(uuid4())
carpeta.mkdir(parents=True)
for nombre, payload in [("propuesta_correo", correo), ("propuesta_correo_texto", texto), ("propuesta_evento", evento), ("actualizar_cita", actualizacion)]:
    (carpeta / (nombre + ".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(carpeta)
