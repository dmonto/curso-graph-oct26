from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import src.validar_permisos as validacion
validacion.ROOT=Path(__file__).resolve().parent
raise SystemExit(validacion.main())

