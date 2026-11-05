from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from operaciones import *
from src.demo_snippets import ejecutar_snippet

if __name__ == "__main__":
    raise SystemExit(ejecutar_snippet('permisos', globals()))
