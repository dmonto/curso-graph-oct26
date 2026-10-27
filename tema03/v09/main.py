from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
print("Perfil propio: User.Read delegado")
print("Asunto y remitente: Mail.ReadBasic delegado")
print("Tareas: Tasks.Read delegado + acceso efectivo al plan")
print("$top y $select reducen datos devueltos, no el alcance del permiso.")
