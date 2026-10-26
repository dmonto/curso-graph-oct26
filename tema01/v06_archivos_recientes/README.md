# Archivos recientes en SharePoint

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v06_archivos_recientes\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Files.Read.
Lista archivos directamente dentro de /CursoGraph, sin recorrer subcarpetas. Filtra por modificación, no por fecha de creación.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
