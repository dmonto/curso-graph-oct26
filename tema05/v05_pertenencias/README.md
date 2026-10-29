# Apartado 5

Altas y bajas de miembros mediante referencias.

Desde la raíz, con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe .\v05_pertenencias\main.py --usuario-id "OBJECT-ID-USUARIO" miembro --grupo-id "OBJECT-ID-GRUPO" --accion alta
.\.venv\Scripts\python.exe .\v05_pertenencias\main.py --usuario-id "OBJECT-ID-USUARIO" --aplicar miembro --grupo-id "OBJECT-ID-GRUPO" --accion alta
.\.venv\Scripts\python.exe .\v05_pertenencias\main.py --usuario-id "OBJECT-ID-USUARIO" --aplicar miembro --grupo-id "OBJECT-ID-GRUPO" --accion baja
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo. Usa `--help` para consultar opciones. No requiere ejecutar otras versiones previamente; conserva los módulos comunes de la raíz.

Sustituye los Object ID. Sin --aplicar, se consulta Graph y se muestra el cambio propuesto. Solo se permite operar con los objetos de prácticas CURSO- que cumplan las condiciones del tema. El permiso de escritura solo es necesario al aplicar. No se reintentan escrituras automáticamente; una respuesta incierta exige comprobar el estado.
