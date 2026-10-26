from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
print("Graph Explorer: https://developer.microsoft.com/graph/graph-explorer")
print("GET https://graph.microsoft.com/v1.0/me?$select=id,displayName,userPrincipalName,mail")
from src.smoke_test import main
raise SystemExit(main())
