"""Comprueba los ejemplos sin credenciales en directorios temporales."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

root = Path(__file__).resolve().parent
with TemporaryDirectory() as tmp:
    for script in sorted(root.glob("v*/main.py")):
        name = script.parent.name
        out = Path(tmp) / name
        result = subprocess.run([sys.executable, str(script), "--local", "--salida", str(out)])
        partial = name.startswith("v12_")
        assert result.returncode == (2 if partial else 0), name
        data = json.loads((out / "resultado.json").read_text(encoding="utf-8"))
        assert data["completo"] == (not partial), name
        if name.startswith("v06_"):
            assert data["archivos"][1]["size"] == 655377
            assert sum(1 for event in data["http"] if event.get("operacion") == "fragmento") == 4
        if partial:
            assert len(data["lectura"]["elementos"]) == 2
        if name.startswith("v14_"):
            assert data["renombrado"]["estado"] == "conflicto_requiere_revision"
    for partial in (False, True):
        out = Path(tmp) / ("parcial" if partial else "normal")
        args = [sys.executable, str(root / "ejercicio_resuelto/main.py"), "--local", "--salida", str(out)]
        result = subprocess.run(args + (["--parcial"] if partial else []))
        assert result.returncode == (2 if partial else 0)
        manifest = next(out.glob("*/manifest.json"))
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["completo"] == (not partial)
        assert len(data.get("archivos", [])) == (0 if partial else 2)
        assert (manifest.parent / "mensaje_teams.json").exists() == (not partial)
print("15 ejemplos y las dos variantes del ejercicio verificados.")
