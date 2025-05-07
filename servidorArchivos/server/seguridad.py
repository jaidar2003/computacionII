import bcrypt
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
