import bcrypt
import os
import sys

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

# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo seguridad.py cargado correctamente.")
    print("✅ Importación de base_datos.db exitosa.")
