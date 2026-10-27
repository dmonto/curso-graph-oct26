from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
print("Delegada: User.Read → /me, actúa con usuario conectado.")
print("Aplicación: User.Read.All → /users, requiere consentimiento administrativo.")
print(".default solicita permisos preconcedidos: no concede permisos nuevos.")
