# Flujo completo: próximos eventos a CSV

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v15_calendario_csv\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Calendars.Read.
calendarView expande recurrencias en la ventana de siete días. Exporta fechas UTC y calcula duración.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
