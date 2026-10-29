# Tema 4 — Autenticación con Microsoft Identity Platform


## Preparación

Python 3.10 o superior. Desde la raíz del paquete:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\v04_prueba_y_diagnostico\main.py --local
```

Completa el único `.env` de la raíz. TENANT_ID es el tenant; CLIENT_ID_DELEGATED es el registro público con flujo de cliente público habilitado y permiso delegado User.Read; CLIENT_ID_APPONLY es el registro confidencial con permiso de aplicación para /users (User.Read.All según el setup) y consentimiento administrativo. CLIENT_SECRET es el valor de su secreto. Las variables del proceso prevalecen sobre .env.

## Ejemplos, en orden

| Carpeta | Contenido del tema |
| --- | --- |
| v01_cliente_confidencial | MSAL confidential client, .default y consulta /users. |
| v02_cache_memoria | Dos adquisiciones; device_code y silent o client_credentials. |
| v03_cache_cifrada | Ampliación: persistencia cifrada entre ejecuciones. |
| v04_prueba_y_diagnostico | Programa completo: configuración, errores, /me, informes y trazabilidad. |
| v05_job_no_interactivo | Ejecución app-only como job. |
| v06_identidad_administrada | Ampliación para recurso Azure con identidad de sistema. |
| ejercicio_resuelto | Programa completo con resumen y conclusiones del ejercicio. |

Cada directorio contiene su programa completo; no importa código de otros ejemplos. `src/` en la raíz contiene exclusivamente módulos comunes de configuración, autenticación, caché y comprobación del entorno. `.env` y dependencias también son comunes.

Las decisiones de flujo OAuth, scope/resource y el checklist son explicaciones sin un programa independiente; están materializadas en las variantes anteriores. Las v01–v05 conservan el CLI completo del tema y cambian los valores predeterminados para el escenario correspondiente.

## Comprobaciones de diagnóstico

```powershell
.\.venv\Scripts\python.exe .\v04_prueba_y_diagnostico\main.py --modo delegada --repeticiones 2
.\.venv\Scripts\python.exe .\v04_prueba_y_diagnostico\main.py --modo apponly --sin-interaccion --repeticiones 2
.\.venv\Scripts\python.exe .\v04_prueba_y_diagnostico\main.py --modo delegada --sin-interaccion --repeticiones 1
```

El tercero es un fallo esperado con caché nueva. Salidas: 0 éxito, 1 error, 130 cancelación. --local comprueba configuración/dependencias sin contactar con Entra ni Graph; no acredita permisos. No se imprimen tokens. El device code se muestra solo para completar el inicio de sesión.

El programa registra Retry-After, pero no reintenta automáticamente Graph. Los informes contienen metadatos de diagnóstico. No distribuir .env configurado ni .cache.

