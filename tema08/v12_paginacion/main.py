from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.archivos_graph import main

if __name__ == "__main__":
    sys.argv[1:1] = ['--accion', 'listar', '--salida', 'output/v12_paginacion', '--max-paginas', '1']
    raise SystemExit(main())
