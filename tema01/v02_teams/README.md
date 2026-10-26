# Teams: enviar mensaje HTML

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v02_teams\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, ChannelMessage.Send.
Crea un mensaje real en el canal de pruebas.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
