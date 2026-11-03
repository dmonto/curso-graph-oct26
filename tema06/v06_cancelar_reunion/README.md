# Cancelación de una reunión

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. Completa el .env raíz para usar el buzón de prácticas.

```powershell
$eventoId = "ID_REAL_DE_REUNION_CURSO"
python .\v06_cancelar_reunion\main.py --evento-id $eventoId
python .\v06_cancelar_reunion\main.py --aplicar --evento-id $eventoId
```

Utiliza una reunión CURSO- que hayas creado en Outlook con el destinatario de pruebas como único asistente, organizada por el buzón. La cancelación puede notificar al asistente. Sin --aplicar consulta y valida; con --aplicar registra cancelacion_aceptada_202. Revisa si el ID representa una ocurrencia o la serie completa antes de aplicar.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
