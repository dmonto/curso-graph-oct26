from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.smoke_test import comprobar_dependencias
import logging
logging.basicConfig(level=logging.INFO)
comprobar_dependencias()
