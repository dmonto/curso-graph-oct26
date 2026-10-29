# Validación del paquete

- Sintaxis Python validada en todos los archivos.
- Contadores del ejercicio comprobados en los tres escenarios y con HTTP 200/JSON inválido.
- Comprobado con doble de prueba que una caché vacía sin interacción falla antes de iniciar device code.
- No se ha realizado autenticación real ni llamadas a Graph.
- La instalación de dependencias y los smoke tests completos no pudieron ejecutarse por la restricción de red del entorno de preparación. Ejecutar los comandos --local del README tras instalar requirements.txt.
- La identidad administrada y la persistencia cifrada requieren validación en su entorno de ejecución.
