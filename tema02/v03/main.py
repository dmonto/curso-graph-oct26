from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ("src/__init__.py","src/utils/__init__.py","src/utils/config.py","src/smoke_test.py"):
    print(name, (root/name).is_file())
