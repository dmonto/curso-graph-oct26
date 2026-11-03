# Validación y envío de correo

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. Completa el .env raíz para usar el buzón de prácticas.

```powershell
$payloads = python .\preparar_payloads.py
python .\v03_correo\main.py --archivo "$payloads/propuesta_correo.json"
# Enviar tras revisar el JSON:
python .\v03_correo\main.py --aplicar --archivo "$payloads/propuesta_correo.json"
```

Sin --aplicar valida y registra simulado; con --aplicar realiza un único POST y registra aceptado_202. Un 202 no confirma entrega; revisa Outlook. Requiere .env incluso para la validación del destinatario. No reintenta un envío incierto.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
