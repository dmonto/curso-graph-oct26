# Columnas de SharePoint

```powershell
python ./v15_columnas_sharepoint/main.py --local
```

Simula la actualización de EstadoProceso y RunId. Para Graph real utiliza --aplicar, --site-id, --list-id y --list-item-id. Las dos columnas de texto deben existir con esos nombres internos. El list-item-id no es el driveItem ID. El ejemplo realiza un PATCH y guarda la respuesta; no crea columnas.
