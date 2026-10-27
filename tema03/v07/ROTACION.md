# Rotación

1. Inventariar propietario, descripción, fecha de caducidad y ubicación de custodia sin copiar el valor.
2. Crear la nueva credencial en el registro correcto.
3. Actualizar el almacén de secretos o .env local.
4. Ejecutar v08 con --modo apponly y comprobar /users.
5. Verificar consumidores antes de retirar la credencial anterior.

No se ejecutan cambios de credenciales desde este paquete. Para producción valorar certificados o identidades administradas según el entorno.
