# Planner: crear tarea asignada al alumno

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v04_planner\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Tasks.ReadWrite.
Crea una tarea real. Usa el ID de usuario obtenido de /me, no su correo.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
