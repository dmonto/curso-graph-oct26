# Apartado 6

Demostración sin red de 429/503, Retry-After y presupuesto de espera.

Desde la raíz, con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe .\v06_reintentos\main.py --escenario 429
.\.venv\Scripts\python.exe .\v06_reintentos\main.py --escenario 503
.\.venv\Scripts\python.exe .\v06_reintentos\main.py --escenario aplazado
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo. Usa `--help` para consultar opciones. No requiere ejecutar otras versiones previamente; conserva los módulos comunes de la raíz.
