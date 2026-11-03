# Ventana local y conversión UTC

Ejecuta desde la raíz del ZIP después de instalar requirements.txt. No necesita acceso a Microsoft 365.

```powershell
python .\v07_zonas_horarias\main.py
python .\v07_zonas_horarias\main.py --dia 2026-10-25
python .\v07_zonas_horarias\main.py --dia 2026-03-29
```

Imprime límites locales y UTC. El 6 de octubre tiene 24 horas; el 25 de octubre, 25; el 29 de marzo, 23. tzdata permite ZoneInfo en Windows.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
