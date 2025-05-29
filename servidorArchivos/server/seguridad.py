import bcrypt
import os
import sys
import bcrypt

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from base_datos.db import autenticar_usuario, registrar_usuario as db_registrar_usuario

def autenticar_usuario_en_servidor(username, password):
    """Autentica un usuario usando la base de datos."""
    usuario = autenticar_usuario(username, password)
    if usuario:
        return usuario  # Devuelve (id, permisos)
    return None

def registrar_usuario(username, password, permisos="lectura"):
    """Registra un nuevo usuario en la base de datos."""
    return db_registrar_usuario(username, password, permisos)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))



# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo seguridad.py cargado correctamente.")
    print("✅ Importación de base_datos.db exitosa.")
