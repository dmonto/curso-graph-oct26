# Consultar licencias

Desde la raíz:

```powershell
.\.venv\Scripts\python .\v13_licencias\main.py
```

Alternativa: añadir `--device-code` si la política del tenant lo permite.
Permisos delegados: User.Read, User.Read.All.
Usa autenticación delegada. licenseDetails no admite app-only según la documentación consultada. Puede requerir un rol Entra compatible, por ejemplo Directory Readers; solicitarlo al administrador si responde 403.
El ejemplo no importa código de otros directorios vXX; usa únicamente los módulos comunes de la raíz.
