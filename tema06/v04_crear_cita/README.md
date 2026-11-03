# Creación de una cita

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. Completa el .env raíz para usar el buzón de prácticas.

```powershell
$payloads = python .\preparar_payloads.py
python .\v04_crear_cita\main.py --archivo "$payloads/propuesta_evento.json"
# Crear la cita tras revisar el JSON:
python .\v04_crear_cita\main.py --aplicar --archivo "$payloads/propuesta_evento.json"
```

Sin --aplicar registra simulado; con --aplicar guarda creado_201 y el evento.id en auditoria.json. Se crea una cita sin asistentes. Conserva el mismo JSON y transactionId para investigar un timeout; no generes automáticamente una propuesta nueva para el mismo intento.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
