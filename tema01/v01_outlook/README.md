# Outlook: cinco correos sin leer

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v01_outlook\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Mail.Read.

El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
