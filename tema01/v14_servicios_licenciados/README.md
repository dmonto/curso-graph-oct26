# Examinar planes de servicio provisionados

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v14_servicios_licenciados\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, User.Read.All.
Mismos requisitos de rol que v13. No deduce prestaciones a partir de cadenas E3/E5.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
