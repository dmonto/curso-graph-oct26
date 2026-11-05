# v05_subida_simple

Desde la raíz del paquete:
```powershell
python ./v05_subida_simple/main.py --local
Get-Content ./output/v05_subida_simple/resultado.json
```

Resultado: Crea CURSO-{run_id}, carga informe.csv y conserva ID y ETag.

Ejecuta con `--help` para consultar argumentos. Sin `--local` utiliza Graph real y el `.env` de la raíz. Las versiones no dependen de ejecutar otras versiones. Los módulos estables están en `src/`.

Para descarga o versiones reales añade `--item-id ID_ARCHIVO`. Para enlace real añade `--crear-enlace-organizacion`. Para paginación completa usa `--max-paginas 100`; para simular interrupción añade `--parcial --local`.
