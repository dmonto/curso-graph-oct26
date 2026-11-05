"""Verificación reproducible sin conexión a Microsoft 365."""
import ast
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import requests

ROOT = Path(__file__).resolve().parent

def leer(ruta):
    return json.loads((ROOT / ruta).read_text(encoding="utf-8"))

def main():
    for ruta in ROOT.rglob("*.py"):
        if ".venv" not in ruta.parts:
            ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    for carpeta in [f"v{i:02}" for i in range(1, 11)] + ["ejercicio_resuelto"]:
        proceso = subprocess.run([sys.executable, "-X", "utf8", "main.py"], cwd=ROOT / carpeta,
                                 capture_output=True, text=True, encoding="utf-8", timeout=60)
        esperado = 2 if carpeta == "ejercicio_resuelto" else 0
        assert proceso.returncode == esperado, (carpeta, proceso.stdout, proceso.stderr)
        print(f"OK {carpeta}: exit={proceso.returncode}")
    datos = leer("v05/resultados/comparacion.json")
    assert [(d["raices"], d["respuestas"], d["coincidencias"], d["completo"]) for d in datos] == [
        (3, 1, 3, True), (2, 1, 2, False)]
    html = leer("v03/resultados/mensaje_teams.json")
    assert "&lt;revisar &amp; confirmar&gt;" in html["body"]["content"]
    assert isinstance(leer("v08/resultados/tarjeta_teams.json")["attachments"][0]["content"], str)
    assert isinstance(leer("v08/resultados/payload_flujo_tema7.json")["attachments"][0]["content"], dict)
    comprobacion = leer("ejercicio_resuelto/resultados/comprobacion_ejercicio.json")
    for item, numeros in zip(comprobacion["preparaciones_outlook"], [(5, 3, 2), (4, 0, 4)]):
        resumen = item["resumen"]
        assert tuple(resumen[k] for k in ("observadas", "listas", "pendientes")) == numeros
        assert resumen["listas"] + resumen["pendientes"] == resumen["observadas"]
        evidencia = leer("ejercicio_resuelto/" + item["salida"])
        assert evidencia["fuente_run_id"] == "00000000-0000-4000-8000-000000000076"
        assert evidencia["modo_origen"] == "simulacion_local"
        carpeta = Path(item["salida"]).parent
        tarjeta = leer(Path("ejercicio_resuelto") / carpeta / "tarjeta_teams.json")
        card = json.loads(tarjeta["attachments"][0]["content"])
        assert f"Observadas: {numeros[0]}; listas: {numeros[1]}; pendientes: {numeros[2]}." in card["body"][1]["text"]
    from src.ejemplos import ejecutar_teams
    codigo, evidencia = ejecutar_teams(ROOT / "v02", ["--local", "--aplicar", "publicar",
                                                    "--archivo", "datos/aviso_tema7.json"])
    assert codigo == 1 and evidencia["http"] == [] and evidencia["datos"] is None
    from src.utils.teams_client import ClienteTeams
    from src.utils.graph_client import ErrorGraph
    class SesionTimeout:
        llamadas = 0
        def request(self, *args, **kwargs):
            self.llamadas += 1
            raise requests.Timeout("simulado")
        def close(self):
            pass
    config = SimpleNamespace(graph_api_url="https://graph.microsoft.com/v1.0", timeout_seconds=1)
    with ClienteTeams(config, lambda: "TOKEN_DE_PRUEBA") as cliente:
        cliente.sesion.close()
        cliente.sesion = SesionTimeout()
        try:
            cliente.escribir("POST", "/teams/demo/channels", cuerpo={})
            raise AssertionError("Debe conservar el resultado incierto.")
        except ErrorGraph as error:
            assert error.incierto and cliente.sesion.llamadas == 1
            assert "TOKEN_DE_PRUEBA" not in json.dumps(cliente.historial)
    print("OK: contadores, alcance, HTML, tarjetas, simulación y escritura incierta.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
