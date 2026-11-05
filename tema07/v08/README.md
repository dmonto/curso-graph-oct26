# Contrato de notificación de un flujo

Convierte attachments.content de cadena JSON de Graph a objeto para el flujo. No invoca un webhook.

Desde la raíz del ZIP:

~~~powershell
python v08/main.py
~~~

También funciona desde esta carpeta con python main.py. Instala antes ../requirements.txt. Los módulos compartidos y .env están en la raíz del paquete; esta carpeta no depende de ningún otro ejemplo. Las salidas se guardan en v08/resultados/.

La ejecución sin argumentos es local y usa referencias ficticias. No necesita credenciales.
