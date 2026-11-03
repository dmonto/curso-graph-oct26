from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.outlook_acciones import main

if __name__ == "__main__":
    argumentos = sys.argv[1:]
    aplicar = ["--aplicar"] if "--aplicar" in argumentos else []
    argumentos = [x for x in argumentos if x != "--aplicar"]
    sys.argv = [sys.argv[0], *aplicar, "cancelar-reunion", *argumentos]
    raise SystemExit(main())
