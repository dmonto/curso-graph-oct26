# Generar y enviar reporte consolidado

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v08_reporte_consolidado\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, Tasks.Read, Files.Read, Mail.Read, Mail.Send.
Envía un correo real al destinatario configurado y conserva una copia HTML local.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
