from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for args in (["git","--version"],["git","-C",str(root),"status","--short"],["git","-C",str(root),"check-ignore",".env"]):
    result=subprocess.run(args,check=False)
    print("Código:",result.returncode)
