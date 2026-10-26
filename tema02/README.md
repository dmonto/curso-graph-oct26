# Tema 2 · Entorno Python

Diez directorios, uno por apartado del GitBook, más ejercicio_resuelto. Cada versión utiliza solo los módulos comunes src/ y .env de la raíz. Los apartados de herramientas incluyen scripts y documentación específica.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python v07/main.py --local
.\.venv\Scripts\python ejercicio_resuelto/main.py --local
```

Linux: usar `.venv/bin/python`. Completar TENANT_ID y CLIENT_ID_DELEGATED en .env para ejecutar sin --local. No necesita secreto. Requiere app pública con device code permitido y User.Read delegado.

- v01: Python y venv
- v02: Dependencias
- v03: Estructura de proyecto
- v04: Variables de entorno
- v05: VS Code
- v06: GitHub y GitLab
- v07: Smoke test
- v08: Logging y errores
- v09: Graph Explorer
- v10: Checklist

En VS Code abrir la raíz y seleccionar el intérprete de .venv. El depurador incluido ejecuta src.smoke_test --local. En v08 probar HTTP_TIMEOUT=0 y restaurarlo. En v09 comparar manualmente identidad y resultado con Graph Explorer.
