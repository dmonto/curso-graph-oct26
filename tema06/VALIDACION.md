# Validación — 27/10/2026

- Compilación de los módulos Python.
- 15 pruebas unittest correctas: lectura completa y parcial, responsables,
  ambigüedad, HTML, rangos, citas, destinatarios, Retry-After, timeout sin
  reenvío, respuesta 202 sin cuerpo, URL externa, adjunto y simulación.
- Laboratorio ejecutado: 5 propuestas completas; 4 propuestas incompletas.
- Ejercicio ejecutado sobre ambas auditorías: 3 listas + 2 pendientes;
  0 listas + 4 pendientes respectivamente, ambos exit code 2.
- Comprobados los JSON de correo de texto de ambas preparaciones.
- Generación de payloads y de correo con adjunto ejecutadas.
- Filtro ejecutado desde su propio directorio, sin PYTHONPATH.
- Europe/Madrid: 24 horas el 6/10, 25 horas el 25/10, 23 horas el 29/3 de 2026.

Entorno de validación: Python 3.14 en Windows.
Dependencias: msal 1.39.0, requests 2.34.2, python-dotenv 1.2.4, tzdata 2026.5.
requirements.txt permite versiones compatibles; no es un lock de todas las
dependencias transitivas.

No se han usado credenciales reales ni se han efectuado envíos o modificaciones
de calendario. Los códigos HTTP de escritura se validan mediante dobles locales.
La autorización de Exchange, entrega del correo y comportamiento del tenant
deben verificarse en el laboratorio real.
