# v07_versiones

Desde la raíz del paquete:
```powershell
python ./v07_versiones/main.py --local
Get-Content ./output/v07_versiones/resultado.json
```

Resultado: Devuelve las versiones 2.0 y 1.0.

Ejecuta con `--help` para consultar argumentos. Sin `--local` utiliza Graph real y el `.env` de la raíz. Las versiones no dependen de ejecutar otras versiones. Los módulos estables están en `src/`.

Para descarga o versiones reales añade `--item-id ID_ARCHIVO`. Para enlace real añade `--crear-enlace-organizacion`. Para paginación completa usa `--max-paginas 100`; para simular interrupción añade `--parcial --local`.
