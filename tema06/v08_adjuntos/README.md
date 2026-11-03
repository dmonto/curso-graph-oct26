# Lectura de mensajes y descarga de adjuntos

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. Completa el .env raíz para usar el buzón de prácticas.

```powershell
$mensajeId = "ID_REAL_DE_MENSAJE"
python .\v08_adjuntos\main.py mensaje --mensaje-id $mensajeId
python .\v08_adjuntos\main.py adjuntos --mensaje-id $mensajeId
python .\v08_adjuntos\main.py adjuntos --mensaje-id $mensajeId --descargar
```

Guarda cuerpo/metadatos o lista de adjuntos y auditoría. --descargar guarda fileAttachment no inline de hasta 2 MiB como .bin, con nombre original y SHA-256 en la auditoría. Otros tipos quedan para revisión y pueden producir código 2.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
