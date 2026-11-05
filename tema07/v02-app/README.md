# Canales, publicación y respuestas (apponly)

Igual que v02, pero autenticando con la cuenta de aplicación (client credentials, scope `.default`).

~~~powershell
python v02-app/main.py
~~~

Requiere en .env: TENANT_ID, CLIENT_ID_APPONLY, CLIENT_SECRET, TEAM_ID y CHANNEL_ID.
Listar canales (`canales`) usa Graph real y necesita el permiso de aplicación Channel.ReadBasic.All con consentimiento de administrador.

Limitación: Graph no permite crear canales ni publicar/responder mensajes solo con permisos de aplicación (salvo migración). Por eso, con `--apponly`, `crear-canal`, `publicar` y `responder` solo generan la propuesta; combinarlas con `--aplicar` se rechaza.

Las salidas se guardan en v02-app/resultados/.
