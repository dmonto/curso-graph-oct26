# Descubrimiento

```powershell
python ./v01_descubrimiento/main.py --local
```

Muestra IDs ficticios de OneDrive, sitio, biblioteca y carpeta. Sin --local consulta Microsoft 365. Configura SHAREPOINT_HOSTNAME y SHAREPOINT_SITE_PATH. La raíz consultada es DRIVE_ID si está configurado; en caso contrario, la de OneDrive. Copia los IDs reales al .env para los demás ejemplos.
