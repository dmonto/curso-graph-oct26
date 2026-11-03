# Laboratorio local paginado

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. No necesita acceso a Microsoft 365.

```powershell
python .\v10_laboratorio\main.py
python .\v10_laboratorio\main.py --max-paginas 1
```

Sin credenciales ni red: 4 mensajes, 3 eventos, 5 propuestas y código 0. Con --max-paginas 1: 2 mensajes, 2 eventos, 4 propuestas origen_incompleto y código 2. Cada ejecución crea una carpeta nueva.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
