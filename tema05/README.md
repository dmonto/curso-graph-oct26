# Tema 5 — Usuarios y grupos con Graph

## Instalación

Python 3.10 o superior. 

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.smoke_test --local
```

Completa el único .env de la raíz. Las variables de entorno del proceso prevalecen sobre el archivo.

| Variable | Contenido |
| --- | --- |
| TENANT_ID | ID del tenant de formación. |
| CLIENT_ID_APPONLY | Application/client ID del registro confidencial. |
| CLIENT_SECRET | Valor del secreto del registro, no su identificador. |
| GROUP_ID | Object ID del grupo de prácticas. |
| CLIENT_ID_DELEGATED | Reservado para compatibilidad con el setup; los ejemplos del Tema 5 usan app-only. |

Para lectura se utilizan User.Read.All y GroupMember.Read.All de aplicación con consentimiento administrativo, según el setup. Para aplicar department, User.ReadWrite.All; para aplicar pertenencias, GroupMember.ReadWrite.All. Los grupos con pertenencia oculta requieren permisos adicionales y quedan fuera del laboratorio estándar. La simulación de cambios también requiere lectura real. Revisa los permisos de cada endpoint si modificas las consultas.

Completa datos/casos_tema5.csv con cuentas del tenant. La entrada usa coma; las exportaciones usan punto y coma y UTF-8 con BOM. FIN-001 y MANT-001 deben compartir el UPN de un usuario interno habilitado miembro directo; RRHH-001, otro usuario interno habilitado que esté fuera; FIN-002, un UPN inexistente del tenant.

## Versiones

| Carpeta | Apartado |
| --- | --- |
| v01_endpoints | Endpoints de usuarios, grupos, miembros directos y transitivos. |
| v02_filtros_paginacion | Proyección, filtro exacto y paginación mediante nextLink. |
| v03_resolver_identidad | Resolución exacta de UPN; detección de ausencia y ambigüedad. |
| v04_atributos | Lectura y actualización controlada de department. |
| v05_pertenencias | Altas y bajas de miembros mediante referencias. |
| v06_reintentos | Demostración sin red de 429/503, Retry-After y presupuesto de espera. |
| v07_resultados_parciales | Demostración sin red de una colección completa o interrumpida. |
| v08_exportacion | Auditoría completa y exportación a CSV/JSON. |
| v09_responsables | Preparación de responsables sin crear tareas ni mensajes. |
| v10_consistencia_naming | Revisión de nombres y departamentos, sin cambios automáticos. |
| ejercicio_resuelto | Auditoría completa, filtro de usuarios por correo de grupo y responsables_listos.csv. |

Cada versión incluye su programa ejecutable, sin importar otra versión. Los módulos que no cambian están en src/ (configuración, MSAL, HTTP, funciones del directorio). No extraigas una versión aislada sin estos módulos.

Los ejemplos v06 y v07 son demostraciones reproducibles sin red; v10 --demo también usa datos ficticios. Las demás ejecuciones requieren configuración y permisos reales. v04 y v05 incluyen el CLI completo de cambios, con comandos específicos para su apartado en sus README.

Las lecturas siguen nextLink y preservan los datos recuperados si hay un error. Una colección parcial no acredita ausencia. Los reintentos GET se limitan a tres intentos con presupuesto de espera de 30 segundos; si Retry-After lo supera, se devuelve reintento_aplazado. Las escrituras se intentan una sola vez. Las bajas usan siempre /$ref.

v08, v09 y el ejercicio guardan resultados en su propia carpeta. No se escriben tokens ni secretos. Los inventarios sí contienen datos del directorio. Salidas: 0 correcto; 2 parcial o incidencias a revisar; 1 error; 130 cancelación.

## Comprobación sin tenant

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe .\v06_reintentos\main.py --escenario aplazado
.\.venv\Scripts\python.exe .\v07_resultados_parciales\main.py --max-paginas 1
.\.venv\Scripts\python.exe .\v10_consistencia_naming\main.py --demo
```