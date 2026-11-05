from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

"""Canales, mensajes y respuestas con la cuenta de aplicación (apponly).
Sin argumentos: lista los canales reales y prepara (sin aplicar) las propuestas."""
from src.ejemplos import ejecutar_teams


def main():
    if sys.argv[1:]:
        return ejecutar_teams(BASE, ["--apponly", *sys.argv[1:]])[0]
    operaciones = [
        ["--apponly", "canales"],
        ["--apponly", "crear-canal", "--nombre", "CURSO-Automatizaciones"],
        ["--apponly", "publicar", "--archivo", "datos/aviso_tema7.json"],
        ["--apponly", "responder", "--mensaje-id", "1001", "--archivo", "datos/aviso_tema7.json"],
    ]
    return max(ejecutar_teams(BASE, args)[0] for args in operaciones)


if __name__ == "__main__":
    raise SystemExit(main())
