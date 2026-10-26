# Lectura defensiva de beta

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v11_beta_defensivo\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Calendars.Read.

El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
