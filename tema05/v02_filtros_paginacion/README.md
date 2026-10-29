# Apartado 2

Proyección, filtro exacto y paginación mediante nextLink.

Desde la raíz, con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe .\v02_filtros_paginacion\main.py --departamento "Financiero" --tamano-pagina 2
.\.venv\Scripts\python.exe .\v02_filtros_paginacion\main.py --tamano-pagina 2 --max-paginas 1
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo. Usa `--help` para consultar opciones. No requiere ejecutar otras versiones previamente; conserva los módulos comunes de la raíz.
