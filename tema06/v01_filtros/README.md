# Filtro por recepción y ordenación

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. No necesita acceso a Microsoft 365.

```powershell
python .\v01_filtros\main.py
```

Imprime el filtro UTC y los campos seleccionados. No llama a Graph. El transporte paginado compartido está en src/utils/outlook_client.py y src/utils/graph_client.py.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
