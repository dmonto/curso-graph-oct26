# Apartado 1

Endpoints de usuarios, grupos, miembros directos y transitivos.

Desde la raíz , con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe .\v01_endpoints\main.py --recurso users
.\.venv\Scripts\python.exe .\v01_endpoints\main.py --recurso groups
.\.venv\Scripts\python.exe .\v01_endpoints\main.py --recurso members
.\.venv\Scripts\python.exe .\v01_endpoints\main.py --recurso transitiveMembers
```

También puedes ejecutar `python main.py` desde esta carpeta con el entorno virtual activo. Usa `--help` para consultar opciones. No requiere ejecutar otras versiones previamente; conserva los módulos comunes de la raíz.

Para `members` y `transitiveMembers`, configura `GROUP_ID` en el `.env` de la raíz o indica `--grupo-id <UUID>` en el comando.
