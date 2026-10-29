# Prueba completa, errores y trazabilidad

Desde la raíz del paquete, después de instalar las dependencias:

```powershell
.\.venv\Scripts\python.exe .\v04_prueba_y_diagnostico\main.py --local
.\.venv\Scripts\python.exe .\v04_prueba_y_diagnostico\main.py
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo.
El programa contiene el flujo completo y solo importa los módulos comunes de la raíz.
Los informes se guardan en `resultados/` dentro de esta carpeta.
Consulta `python main.py --help` para elegir modo, recurso, repeticiones y caché.
