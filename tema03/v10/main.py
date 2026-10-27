from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
print((Path(__file__).parent/"CHECKLIST.md").read_text(encoding="utf-8"))
