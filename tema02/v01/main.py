from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sys
print(sys.version)
print(sys.executable)
print("Entorno virtual:", sys.prefix != sys.base_prefix)
raise SystemExit(0 if sys.version_info >= (3,10) and sys.prefix != sys.base_prefix else 1)
