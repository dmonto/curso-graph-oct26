# Tema 1 · Introducción a Microsoft Graph en Microsoft 365

Cada vXX contiene un programa completo: no hay que ejecutar ni copiar fragmentos de versiones anteriores.
Los módulos config.py, auth.py, graph_client.py y util.py, las dependencias y .env se comparten desde la raíz. Conservar esa estructura al extraer.

## Instalación (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python .\v01_outlook\main.py
```

Completar antes .env con el setup del curso. Se incluyen nombres de variables, sin credenciales.
Usar CLIENT_ID_DELEGATED, TENANT_ID y USER_UPN. REDIRECT_URI debe ser http://localhost.
La app pública debe permitir el flujo elegido; cada script solicita sus scopes delegados y verifica la cuenta con /me.
Para código de dispositivo añadir --device-code. No se persisten tokens en disco.
No se necesita la app-only ni CLIENT_SECRET para estos ejemplos.

## Ejemplos por orden

| Directorio | Contenido |
| --- | --- |
| v01_outlook | Outlook: cinco correos sin leer |
| v02_teams | Teams: enviar mensaje HTML |
| v03_onedrive | OneDrive: subir archivo incluido |
| v04_planner | Planner: crear tarea asignada al alumno |
| v05_tareas_completadas | Tareas completadas durante los últimos siete días |
| v06_archivos_recientes | Archivos recientes en SharePoint |
| v07_correos_relevantes | Correos relevantes por asunto |
| v08_reporte_consolidado | Generar y enviar reporte consolidado |
| v09_eventos_v1 | Eventos con v1.0 |
| v10_eventos_beta | Eventos con beta |
| v11_beta_defensivo | Lectura defensiva de beta |
| v12_v1_beta_opcional | Base v1.0 y lectura beta opcional |
| v13_licencias | Consultar licencias |
| v14_servicios_licenciados | Examinar planes de servicio provisionados |
| v15_calendario_csv | Flujo completo: próximos eventos a CSV |
| ejercicio_resuelto | Solución de los tres ejercicios conceptuales y reporte ejecutable |

v02 publica un mensaje; v03 sube un archivo; v04 crea una tarea; v08 envía un correo.
Repetirlos puede crear recursos adicionales. Revisar la respuesta antes de repetir una escritura tras un timeout.
Los resultados descargados se guardan en salidas/ del propio ejemplo.
Los demás ejemplos solo leen o generan resultados locales.

## Diagnóstico

401: revisar sesión y tenant. 403: scopes, consentimiento, rol y acceso al recurso.
404: IDs y aprovisionamiento. 429/503: respetar Retry-After; no hay reintentos automáticos de escrituras.
Una respuesta 202 de sendMail indica aceptación, no entrega confirmada.
Los ejemplos de correo recorren la bandeja de entrada; en buzones grandes pueden tardar.
v06 y el reporte consideran solo archivos directamente dentro de /CursoGraph.
Para v13/v14, licenseDetails requiere permisos delegados y un rol Entra compatible según la documentación.

