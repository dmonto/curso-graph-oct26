# Base v1.0 y lectura beta opcional

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v12_v1_beta_opcional\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Calendars.Read.
Demuestra tolerancia a errores en una lectura opcional. Los campos empleados también están disponibles en v1.0. Los pseudoejemplos de IA/fallback del tema se concretan aquí sin inventar propiedades.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
