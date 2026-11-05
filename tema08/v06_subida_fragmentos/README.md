# v06_subida_fragmentos

Desde la raíz del paquete:
```powershell
python ./v06_subida_fragmentos/main.py --local
Get-Content ./output/v06_subida_fragmentos/resultado.json
```

Resultado: Carga CSV y binario; el binario usa 327680 + 327680 + 17 bytes.

Ejecuta con `--help` para consultar argumentos. Sin `--local` utiliza Graph real y el `.env` de la raíz. Las versiones no dependen de ejecutar otras versiones. Los módulos estables están en `src/`.

Para descarga o versiones reales añade `--item-id ID_ARCHIVO`. Para enlace real añade `--crear-enlace-organizacion`. Para paginación completa usa `--max-paginas 100`; para simular interrupción añade `--parcial --local`.
