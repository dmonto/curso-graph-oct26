# v02_inventario

Desde la raíz del paquete:
```powershell
python ./v02_inventario/main.py --local
Get-Content ./output/v02_inventario/resultado.json
```

Resultado: Tres elementos, dos páginas y completo=true.

Ejecuta con `--help` para consultar argumentos. Sin `--local` utiliza Graph real y el `.env` de la raíz. Las versiones no dependen de ejecutar otras versiones. Los módulos estables están en `src/`.

Para descarga o versiones reales añade `--item-id ID_ARCHIVO`. Para enlace real añade `--crear-enlace-organizacion`. Para paginación completa usa `--max-paginas 100`; para simular interrupción añade `--parcial --local`.
