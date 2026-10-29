# Apartado 4

Lectura y actualización controlada de department.

Desde la raíz, con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe .\v04_atributos\main.py --usuario-id "OBJECT-ID-USUARIO" departamento --valor "Financiero"
.\.venv\Scripts\python.exe .\v04_atributos\main.py --usuario-id "OBJECT-ID-USUARIO" --aplicar departamento --valor "Financiero"
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo. Usa `--help` para consultar opciones. No requiere ejecutar otras versiones previamente; conserva los módulos comunes de la raíz.

Sustituye los Object ID. Sin --aplicar, se consulta Graph y se muestra el cambio propuesto. Solo se permite operar con los objetos de prácticas CURSO- que cumplan las condiciones del tema. El permiso de escritura solo es necesario al aplicar. No se reintentan escrituras automáticamente; una respuesta incierta exige comprobar el estado.
