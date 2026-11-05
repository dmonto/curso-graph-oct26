# Tema 7 · Microsoft Teams con Graph

Código del Tema 7 del Curso Graph, organizado por orden de aparición.
Fuente: https://diego-montoliu.gitbook.io/curso-graph/sesion-4/microsoft-teams-con-graph
Consulta del contenido: 28 de octubre de 2026.

## Preparación

Python 3.10 o posterior. Desde la carpeta descomprimida:

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python v01/main.py
~~~

En macOS/Linux, activa el entorno con source .venv/bin/activate.

Los ejemplos sin argumentos usan datos locales ficticios y no necesitan configurar credenciales.
El archivo .env se incluye en la raíz, vacío de identificadores reales y secretos.

## Organización

| Carpeta | Ejemplo |
| --- | --- |
| v01 | Cliente reutilizable para Teams |
| v02 | Canales, publicación y respuestas |
| v03 | Plantillas completas |
| v04 | Mención de una persona |
| v05 | Lectura y búsqueda en hilos |
| v06 | Miembros y roles |
| v07 | Carpeta de SharePoint del canal |
| v08 | Contrato de notificación de un flujo |
| v09 | Diagnóstico de auditorías |
| v10 | Resumen según estado |
| ejercicio_resuelto | Solución completa, entradas completa/parcial y conclusiones |

Cada carpeta incluye main.py y README.md; las entradas que necesita están en su propio directorio datos.
Los módulos que se mantienen iguales se comparten en src/ en la raíz. No es necesario ejecutar una versión anterior.
Los resultados se generan dentro de la carpeta del ejemplo, independientemente del directorio desde el que se lance Python.
Para transportar un ejemplo, conserva también src/, .env y requirements.txt de la raíz.

## Ejecutar los ejemplos

~~~powershell
python v02/main.py
python v03/main.py
python v04/main.py
python v05/main.py
python v06/main.py
python v07/main.py
python v08/main.py
python v09/main.py
python v10/main.py
python ejercicio_resuelto/main.py
~~~

También puedes entrar en cualquier carpeta y ejecutar python main.py.
Los lanzadores de comparación v05 y v09 devuelven 0 cuando la demostración se completa correctamente, aunque sus auditorías registren una lectura parcial con código 2.
El ejercicio conserva el código 2 por las propuestas pendientes: es el resultado esperado, no un fallo.

## Consultas y publicación real

En el .env de la raíz, configura TENANT_ID, CLIENT_ID_DELEGATED, TEAM_ID y CHANNEL_ID.
Utiliza la aplicación delegada del setup del curso con flujo de cliente público habilitado.
Las variables ya establecidas en el entorno tienen prioridad sobre .env.
No se necesita CLIENT_SECRET para el flujo delegado.

| Operación | Permisos delegados solicitados por el código |
| --- | --- |
| canales | Channel.ReadBasic.All |
| miembros | TeamMember.Read.All |
| hilos | ChannelMessage.Read.All |
| carpeta | Files.Read.All |
| crear-canal | Channel.Create |
| publicar / responder | Channel.ReadBasic.All, ChannelMessage.Send |

Los permisos requieren el consentimiento que corresponda y la cuenta debe tener acceso al recurso.
Una cuenta autorizada completa el inicio de sesión por código de dispositivo.
La caché de MSAL es en memoria; un proceso nuevo puede volver a solicitar autenticación.

~~~powershell
python v02/main.py canales
python v02/main.py miembros
python v02/main.py hilos --termino "CURSO-"
python v07/main.py carpeta
python v02/main.py crear-canal --nombre "CURSO-Automatizaciones"
python v02/main.py publicar --archivo datos/aviso_tema7.json
~~~

Las dos últimas órdenes preparan propuestas sin escribir. Para realizar la operación real:

~~~powershell
python v02/main.py --aplicar crear-canal --nombre "CURSO-Automatizaciones"
python v02/main.py --aplicar publicar --archivo datos/aviso_tema7.json
python v02/main.py --aplicar responder --mensaje-id "ID_REAL_DEL_MENSAJE" --archivo datos/aviso_tema7.json
~~~

Tras crear el canal, copia su id de la auditoría a CHANNEL_ID antes de publicar.
Las publicaciones comprueban que el canal sea CURSO-, estándar y activo.
La combinación --local --aplicar se rechaza.
Las rutas relativas de --archivo se resuelven desde la carpeta del ejemplo que se está ejecutando.
Las escrituras de miembros de v06 se entregan como propuestas locales, igual que en el tema.

## Módulos compartidos

- src/utils/config.py, auth_msal.py y graph_client.py: configuración, MSAL y paginación del setup anterior.
- src/utils/teams_client.py: cliente del Tema 7 con escrituras de un intento y estado incierto.
- src/teams_graph.py: programa completo de consultas y propuestas del tema.
- src/plantillas_teams.py: HTML, menciones, tarjetas y validación.
- src/auditar_directorio.py: utilidades de identificación reutilizadas.
- src/ejemplos.py: adaptación de rutas para aislar entradas y resultados por ejemplo.

El código del ejercicio permanece en ejercicio_resuelto/preparar_resumen_teams.py.
Las adaptaciones de empaquetado son los lanzadores y el aislamiento de rutas; los módulos Teams del tema se conservan.

## Validación local

~~~powershell
python verificar.py
~~~

La verificación ejecuta cada carpeta por separado, comprueba los contadores, el escape HTML, los contratos de tarjeta y los resultados de simulación.
Prueba además que un timeout de escritura conserve incertidumbre sin repetir el POST.
No realiza llamadas a Microsoft 365. Las operaciones reales dependen del tenant y sus permisos.
