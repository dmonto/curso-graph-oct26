# Persistencia cifrada entre procesos

Desde la raíz del paquete, después de instalar las dependencias:

```powershell
.\.venv\Scripts\python.exe .\v03_cache_cifrada\main.py --local
.\.venv\Scripts\python.exe .\v03_cache_cifrada\main.py
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo.
El programa contiene el flujo completo y solo importa los módulos comunes de la raíz.
Los informes se guardan en `resultados/` dentro de esta carpeta.
Consulta `python main.py --help` para elegir modo, recurso, repeticiones y caché.

La caché cifrada es el valor predeterminado. Usa `--no-cache-cifrada` para desactivarla. Windows utiliza DPAPI; Linux requiere un servicio de secretos compatible y macOS el llavero. No se permite fallback a texto plano.
