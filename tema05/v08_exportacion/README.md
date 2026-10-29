# Apartado 8

Auditoría completa y exportación a CSV/JSON.

```powershell
.\.venv\Scripts\python.exe .\v08_exportacion\main.py --tamano-pagina 2
.\.venv\Scripts\python.exe .\v08_exportacion\main.py --departamento "Financiero" --tamano-pagina 2
.\.venv\Scripts\python.exe .\v08_exportacion\main.py --tamano-pagina 2 --max-paginas 1
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo. Usa `--help` para consultar opciones. No requiere ejecutar otras versiones previamente; conserva los módulos comunes de la raíz.
