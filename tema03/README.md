# Tema 3 · Registro de aplicaciones y permisos

Diez versiones por orden del GitBook y ejercicio_resuelto. Los apartados de configuración incluyen guías operativas; no crean registros ni conceden permisos automáticamente. src/ y .env son comunes y están en la raíz. Cada versión funciona sin importar otras vXX.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python v02/main.py --modo delegada
.\.venv\Scripts\python v02/main.py --modo apponly
```

Linux: usar .venv/bin/python. Completar .env con el setup: TENANT_ID, CLIENT_ID_DELEGATED y, para app-only, CLIENT_ID_APPONLY y CLIENT_SECRET. No se incluyen secretos reales. Device code requiere flujo público permitido. La validación app-only usa User.Read.All con consentimiento administrativo. Configuración valida UUID, URL y timeout.

- v01: Registro de aplicaciones
- v02: Delegados y aplicación
- v03: Scopes y consentimiento
- v04: Redirecciones y tipos de cuenta
- v05: Permisos por servicio
- v06: Diagnóstico de permisos
- v07: Gestión de secretos
- v08: Validación con Graph Explorer
- v09: Menor privilegio
- v10: Checklist operativo


