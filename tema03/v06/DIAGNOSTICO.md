# Diagnóstico

- Error MSAL: revisar tenant, client ID, flujo público, secreto/caducidad y políticas.
- 401: token o audiencia.
- 403: permisos, consentimiento y acceso efectivo.
- App-only + /me: no hay usuario conectado. Primero confirmar /users con el mismo modo.
- Guardar HTTP y request-id para soporte, sin credenciales.
