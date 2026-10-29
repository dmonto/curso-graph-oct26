import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from src.runtime import conectar, mostrar, ejecutar
from src.directorio import resolver_usuario

def main():
    p = argparse.ArgumentParser(description="Resolver exactamente un UPN")
    p.add_argument("--upn", required=True)
    a = p.parse_args()
    with conectar() as g:
        usuario = resolver_usuario(g, a.upn.strip())
        mostrar({"estado":"encontrado" if usuario else "no_encontrado", "usuario":usuario})
        return 0 if usuario else 2

if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
