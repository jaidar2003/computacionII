from hashlib import sha256
from base_datos.db import autenticar_usuario, registrar_usuario

def autenticar_usuario_en_servidor(username, password):
    """Autentica un usuario usando la base de datos."""
    usuario = autenticar_usuario(username, password)
    if usuario:
        return usuario  # Devuelve (id, permisos)
    return None

def registrar_usuario(username, password, permisos="lectura"):
    """Registra un nuevo usuario en la base de datos."""
    password_hash = sha256(password.encode()).hexdigest()
    return registrar_usuario(username, password_hash, permisos)
