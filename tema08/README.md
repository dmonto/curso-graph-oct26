# Tema 8 — OneDrive y SharePoint con Microsoft Graph

Código basado en la página ONEDRIVE Y SHAREPOINT de GitBook, consultada el 30-10-2026.
Cada directorio vNN contiene un ejemplo ejecutable independiente. No requiere ejecutar una versión anterior. `.env`, dependencias y módulos estables se comparten desde la raíz; conserva esa estructura al extraer el ZIP.

## Preparación

Python 3.11 o posterior. Desde PowerShell, en la raíz extraída:
```powershell
py -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python ./v02_inventario/main.py --local
```

El `.env` incluido está vacío de credenciales. Todas las demos locales funcionan sin tenant. Cada proceso reinicia los datos ficticios; las cargas simuladas no se conservan entre procesos. `output/` contiene evidencias locales.

## Ejemplos en orden

| Directorio | Resultado local |
|---|---|
| v02_inventario | Tres elementos, dos páginas y completo=true. |
| v03_busqueda | Encuentra resumen-proveedores.csv. |
| v04_descarga | descargado.csv y SHA-256 en resultado.json. |
| v05_subida_simple | Crea CURSO-{run_id}, carga informe.csv y conserva ID y ETag. |
| v06_subida_fragmentos | Carga CSV y binario; el binario usa 327680 + 327680 + 17 bytes. |
| v07_versiones | Devuelve las versiones 2.0 y 1.0. |
| v08_restaurar_version | Restaura 1.0 y recupera el ETag actual. |
| v09_enlace | Enlace organization/view con expiración solicitada a siete días. |
| v10_auditoria_permisos | Permiso heredado y hallazgo PERM-ANONIMO-DEMO. |
| v11_gestion_permisos | Concede lectura, cambia a escritura y revoca solo el permiso creado en esa ejecución. |
| v12_paginacion | Lectura parcial de dos elementos, completo=false y salida 2. |
| v13_carpeta_canal | Obtiene drive y carpeta desde filesFolder; no publica mensajes. |
| v14_conflicto_etag | Carga confirmada y renombrado pendiente por 412; sin reintento. |

También se incluyen v01_descubrimiento (sitio, bibliotecas y raíz), v15_columnas_sharepoint (campos de listItem) y ejercicio_resuelto/.

## Graph real

Configura TENANT_ID y CLIENT_ID_DELEGATED con una aplicación pública con redirect URI `http://localhost` (login interactivo en el navegador), y los IDs de drive/carpeta en `.env`. La cuenta debe tener acceso a los recursos. Las escrituras del laboratorio validan una carpeta llamada CursoGraph o CURSO-... . Elimina `--local` para utilizar Graph real; puede abrir autenticación y las versiones de escritura crean o modifican recursos.

Permisos delegados solicitados: Files.Read.All para lectura; Files.ReadWrite.All para cargas, enlaces, restauración y permisos; Sites.Read.All para descubrimiento del sitio; Sites.ReadWrite.All para columnas. El consentimiento no sustituye al acceso del usuario. Cada tenant puede requerir aprobación del administrador. No se necesitan secretos de cliente.

Para v13 configura TEAM_ID y CHANNEL_ID. Para descargar, consultar o restaurar versiones reales especifica --item-id. El descubrimiento v01 muestra los IDs que puedes copiar al .env. Las columnas de v15 deben existir previamente y utilizar sus nombres internos.

Las URLs preautorizadas no se guardan en informes ni llevan el token Graph. Los ejemplos preservan los estados parciales y no reintentan automáticamente escrituras de resultado incierto. Las sesiones por fragmentos son secuenciales; no implementan reanudación persistente entre procesos.

## Verificación sin credenciales

```powershell
python verificar_local.py
```

Ejecuta todos los ejemplos con simulación y comprueba el ejercicio normal y parcial. No llama a Microsoft 365. La validación real requiere tu tenant.

## Correspondencia

src/lab_archivos.py, src/utils/files_client.py y src/archivos_graph.py contienen el código común del tema. Los snippets adicionales están en operaciones.py de su versión. src/demo_snippets.py amplía únicamente la simulación de restauración y permisos para poder ejecutar esos ejemplos. Se incluye descubrimiento y actualización de columnas como programas completos a partir de los ejemplos HTTP del tema.

Fuente: https://diego-montoliu.gitbook.io/curso-graph/sesion-4/onedrive-y-sharepoint
