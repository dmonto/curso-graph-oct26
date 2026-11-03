# Actualización y eliminación de una cita

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. Completa el .env raíz para usar el buzón de prácticas.

```powershell
$eventoId = "ID_REAL_DE_CITA_SIMPLE_CURSO"
$payloads = python .\preparar_payloads.py
python .\v05_actualizar_eliminar\main.py actualizar-cita --evento-id $eventoId --archivo "$payloads/actualizar_cita.json"
python .\v05_actualizar_eliminar\main.py actualizar-cita --aplicar --evento-id $eventoId --archivo "$payloads/actualizar_cita.json"
python .\v05_actualizar_eliminar\main.py eliminar-cita --evento-id $eventoId
python .\v05_actualizar_eliminar\main.py eliminar-cita --aplicar --evento-id $eventoId
```

Utiliza una cita CURSO- ya existente, organizada por el buzón y sin asistentes. No requiere ejecutar otra versión: puedes crearla manualmente en Outlook. Sin --aplicar consulta el evento y valida. Con --aplicar registra actualizado_200 o eliminado_204. Ajusta las fechas del JSON antes de actualizar.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
