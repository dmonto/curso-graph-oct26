# OneDrive: subir archivo incluido

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v03_onedrive\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Files.ReadWrite.
Crea un archivo real con nombre único en el OneDrive del alumno.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
