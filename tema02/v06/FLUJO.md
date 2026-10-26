# Flujo Git

Desde la raíz, si aún no hay repositorio:
```bash
git init
git switch -c tema02-entorno
git status --short
git check-ignore .env
git add .gitignore .env.example requirements.txt README.md src v01 v02 v03 v04 v05 v06 v07 v08 v09 v10 ejercicio_resuelto .vscode
git diff --cached
```
Revisar el diff antes de hacer commit. Configurar el remoto propio con `git remote add origin URL`, hacer commit y push de la rama y abrir una PR/MR en GitHub/GitLab. No incluir .env ni resultados personales.
