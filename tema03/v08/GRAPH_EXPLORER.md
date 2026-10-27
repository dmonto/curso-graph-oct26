# Comparativa manual

Abrir https://developer.microsoft.com/graph/graph-explorer con la misma cuenta y ejecutar GET https://graph.microsoft.com/v1.0/me?$select=id,displayName . Comparar estado con v08 --modo delegada. Explorer usa su propia aplicación: sus consentimientos no acreditan los de CLIENT_ID_DELEGATED. No reproduce el modo app-only de estos scripts.
