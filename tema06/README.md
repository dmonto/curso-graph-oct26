# Tema 6 — Correo electrónico y calendarios

Código basado en el Tema 6 de Curso Graph en GitBook, consultado el 27/10/2026.

## Preparación

Python 3.10 o posterior. Desde la carpeta extraída tema06-graph:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python .\v10_laboratorio\main.py
```

Si no activas el entorno, utiliza .\.venv\Scripts\python.exe en lugar de python.
Las dependencias instaladas durante la validación quedan registradas en VALIDACION.md.

## Organización

Cada vNN contiene su entrada ejecutable completa y su README con comandos y resultados.
Ninguna versión importa otra versión. El .env, los datos de prueba y los módulos que no
cambian se mantienen una sola vez en la raíz (src/). Conserva esta estructura al extraer:
autocontenido significa independiente de los otros ejemplos y de los ZIP anteriores,
con acceso a la raíz compartida. No hay fragmentos que tengas que pegar o completar.

| Directorio | Ejemplo | Acceso |
| --- | --- | --- |
| v01_filtros | Filtro por recepción y ordenación | local |
| v02_lectura | Lectura completa de buzón y agenda | real |
| v03_correo | Validación y envío de correo | real |
| v04_crear_cita | Creación de una cita | real |
| v05_actualizar_eliminar | Actualización y eliminación de una cita | real |
| v06_cancelar_reunion | Cancelación de una reunión | real |
| v07_zonas_horarias | Ventana local y conversión UTC | local |
| v08_adjuntos | Lectura de mensajes y descarga de adjuntos | real |
| v09_correo_adjunto | Preparación de correo con adjunto | local |
| v10_laboratorio | Laboratorio local paginado | local |

- src/utils/: autenticación, configuración y clientes HTTP reutilizables.
- src/outlook_lectura.py: lectura, propuestas y exportación.
- src/outlook_acciones.py: validadores y operaciones de correo/calendario.
- src/lab_outlook.py: respuestas ficticias para probar sin red.
- src/auditar_directorio.py: utilidades necesarias del Tema 5 incluidas en el paquete.
- ejercicio_resuelto/: resolución completa, enunciado y conclusiones.
- preparar_payloads.py: genera correo HTML, correo de texto, cita y actualización,
  sin depender de ejecutar otra versión.
- tests/: comprobaciones sin llamadas a Microsoft 365.
- resultados/: se crea en cada ejecución; no se incluye en el ZIP.

## Configuración real

Completa únicamente el .env de la raíz. Incluido vacío de credenciales:

| Variable | Valor |
| --- | --- |
| TENANT_ID | ID del tenant |
| CLIENT_ID_APPONLY | ID de la aplicación confidencial |
| CLIENT_SECRET | Valor del secreto de esa aplicación |
| COURSE_MAILBOX_USER_ID | Object ID del usuario con buzón Exchange Online |
| COURSE_TEST_RECIPIENT | Una dirección de pruebas real autorizada |
| GRAPH_API_URL | https://graph.microsoft.com/v1.0 |
| HTTP_TIMEOUT | 15 segundos |
| LOG_LEVEL | INFO |

CLIENT_ID_DELEGATED se conserva por compatibilidad con el módulo de autenticación;
los ejemplos reales de este tema usan app-only y /users/{id}, no /me.

Para todas las lecturas del paquete: permisos de aplicación Mail.Read y Calendars.Read.
Para enviar: Mail.Send. Para crear, modificar, eliminar y cancelar: Calendars.ReadWrite.
Configura consentimiento de administrador y acceso de la aplicación al buzón de prácticas
según la configuración de Exchange de tu organización. No basta con permisos de directorio.

El laboratorio local y el ejercicio con sus CSV ficticios no requieren rellenar .env.
No mezcles IDs ficticios de datos/ con consultas reales.

## Probar cada ejemplo

Consulta el README del directorio correspondiente. Todos sus comandos se muestran
desde la raíz. Para consultas reales, usa un rango con datos de tu buzón; las fechas
de octubre incluidas reproducen el ejemplo del texto, no significan "hoy".

Para generar propuestas independientes:

```powershell
$payloads = python .\preparar_payloads.py
Get-Content "$payloads/propuesta_correo.json"
Get-Content "$payloads/propuesta_correo_texto.json"
Get-Content "$payloads/propuesta_evento.json"
```

La cita se propone para mañana a las 09:00 UTC. Puedes usar --dia YYYY-MM-DD.
La función propuesta_cita del laboratorio conserva el cálculo original:
nueve horas después del límite UTC de la ventana; no representa siempre las 09:00 locales.

Cada generación crea un transactionId nuevo. Guarda el archivo de una operación concreta;
no vuelvas a generarlo para reintentar a ciegas la misma creación.

Las escrituras se simulan por defecto y se aplican solo con --aplicar.
La simulación de actualizar, eliminar o cancelar consulta el evento real para validar
organizador, tipo y asistentes; no es un modo sin conexión.
Un timeout de escritura queda como incierto en la auditoría y no se reintenta.
Un 202 de correo significa aceptación, no entrega confirmada.

## Ejercicio resuelto

```powershell
python .\v10_laboratorio\main.py
python .\v10_laboratorio\main.py --max-paginas 1
# Sustituye las rutas por las dos carpetas impresas:
python .\ejercicio_resuelto\main.py --auditoria "resultados/tema6_demo_ID_COMPLETO/auditoria.json" --responsables datos/responsables_tema6_demo.csv
python .\ejercicio_resuelto\main.py --auditoria "resultados/tema6_demo_ID_PARCIAL/auditoria.json" --responsables datos/responsables_tema6_demo.csv
```

Resultado completo: cinco propuestas, tres listas para revisión y dos sin responsable
verificado; preparación parcial (código 2). Resultado incompleto: cuatro propuestas de
origen incompleto y ninguna lista. Se producen CSV, resumen, preparación.json y correos
HTML/texto para revisión. No se crean tareas en Planner ni se envían mensajes.

## Códigos de salida

0: operación completada o validación simulada correcta.
1: error de entrada, permisos, red o escritura de archivos.
2: lectura o preparación parcial; revisa la auditoría.
130: interrupción manual durante la lectura real.

## Correspondencia y ajustes

Se conserva el código del GitBook en los módulos compartidos, incluido el cliente
Outlook. Se han completado las dependencias del Tema 5, creado entradas por ejemplo,
parametrizado el adjunto y la zona horaria, y automatizado la copia de correo de texto
del ejercicio. El transporte es compartido y se prueba en tests/.
Las explicaciones conceptuales sin código no requieren otra versión.
La solución está únicamente en ejercicio_resuelto/ dentro del ZIP.
El contenido publicado de GitBook no se modifica con esta entrega.

## Referencias

- [Tema 6](https://diego-montoliu.gitbook.io/curso-graph/sesion-3/correo-electronico-y-calendarios)
- [Listado de mensajes](https://learn.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0)
- [sendMail](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0)
- [Crear eventos](https://learn.microsoft.com/en-us/graph/api/calendar-post-events?view=graph-rest-1.0)
