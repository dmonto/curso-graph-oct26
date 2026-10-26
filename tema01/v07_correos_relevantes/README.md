# Correos relevantes por asunto

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v07_correos_relevantes\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Mail.Read.
El filtrado local evita combinaciones de filtros y ordenación que Exchange rechaza. Recorre la bandeja de entrada.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
