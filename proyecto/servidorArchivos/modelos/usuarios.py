from baseDatos.models import get_db_connection
from hashlib import sha256

def insertar_usuario(username, password, permisos="lectura"):
    """Inserta un nuevo usuario en la base de datos, si no existe."""
    password_hash = sha256(password.encode()).hexdigest()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Verificar si el usuario ya existe
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            if cursor.fetchone():
                return {"status": "error", "message": f"⚠ El usuario '{username}' ya existe."}

            # Insertar usuario
            cursor.execute("""
                INSERT INTO usuarios (username, password, permisos)
                VALUES (?, ?, ?)
            """, (username, password_hash, permisos))
            conn.commit()
            return {"status": "success", "message": f"✅ Usuario '{username}' creado correctamente."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Error al insertar usuario: {e}"}

def autenticar_usuario(username, password):
    """Autentica un usuario verificando su contraseña."""
    password_hash = sha256(password.encode()).hexdigest()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, permisos FROM usuarios WHERE username = ? AND password = ?
            """, (username, password_hash))
            return cursor.fetchone()
    except Exception as e:
        print(f"❌ Error al autenticar usuario: {e}")
        return None
