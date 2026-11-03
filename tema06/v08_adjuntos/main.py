from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.outlook_acciones import main

if __name__ == "__main__":
    argumentos = sys.argv[1:]
    aplicar = ["--aplicar"] if "--aplicar" in argumentos else []
    argumentos = [x for x in argumentos if x != "--aplicar"]
    if not argumentos or argumentos[0] not in ["mensaje","adjuntos"]:
        raise SystemExit("Primera opción: mensaje | adjuntos. Usa --help tras la operación.")
    sys.argv = [sys.argv[0], *aplicar, *argumentos]
    raise SystemExit(main())
