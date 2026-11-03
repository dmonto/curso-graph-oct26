# Preparación de correo con adjunto

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. No necesita acceso a Microsoft 365.

```powershell
$payloads = python .\preparar_payloads.py
python .\v09_correo_adjunto\main.py --archivo "$payloads/propuesta_correo.json"
```

Genera propuesta_correo_con_adjunto.json junto al JSON de entrada, con contentBytes en base64. No envía. El límite didáctico del adjunto es 128 KiB. Para enviar usa v03 con este archivo y un destinatario real configurado.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
