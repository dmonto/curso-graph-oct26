# Identidad administrada de sistema

Ejecuta `python main.py` en un recurso Azure compatible con identidad administrada de sistema habilitada y permisos de aplicación de Graph para consultar `/users` (por ejemplo User.Read.All, concedido por el administrador a esa identidad).

No necesita CLIENT_SECRET ni los client IDs del .env. No funciona como prueba local en un PC ni está destinado a Cloud Shell. Utiliza `resource` en la API ManagedIdentityClient, mientras el cliente confidencial utiliza `scopes=["https://graph.microsoft.com/.default"]`.
