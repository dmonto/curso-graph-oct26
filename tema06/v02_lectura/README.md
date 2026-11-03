# Lectura completa de buzón y agenda

Ejecuta desde la raíz después de instalar requirements.txt. Completa el .env raíz para usar el buzón de prácticas.

```powershell
python .\v02_lectura\main.py --desde "2026-10-06T00:00:00+02:00" --hasta "2026-10-07T00:00:00+02:00" --tamano-pagina 2
python .\v02_lectura\main.py --desde "2026-10-06T00:00:00+02:00" --hasta "2026-10-07T00:00:00+02:00" --tamano-pagina 2 --max-paginas 1
```

Genera mensajes.csv, eventos.csv, propuestas_tareas.csv, propuesta_correo.json, propuesta_evento.json y auditoria.json. Código 0 si ambas colecciones están completas; 2 si hay páginas pendientes. Los contadores reales dependen del buzón. Ajusta el rango a fechas con datos.

Código de entrada: main.py. Los módulos estables se importan de ../src; no se importa ninguna versión hermana. También se puede ejecutar desde este directorio usando python main.py y rutas absolutas para los archivos de entrada.
