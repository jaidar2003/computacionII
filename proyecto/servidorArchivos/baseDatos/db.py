import os
import sqlite3
from hashlib import sha256

# Definir la ruta de la base de datos
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Subimos un nivel
# DB_PATH = os.path.join(BASE_DIR, 'baseDatos', 'servidor_archivos.db')
DB_PATH = "/home/juanma/PycharmProjects/computacionII/proyecto/servidorArchivos/baseDatos/servidor_archivos.db"

# Asegurar que la carpeta 'baseDatos' exista
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH))

def crear_tablas():
    """Crea las tablas necesarias si no existen."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                permisos TEXT NOT NULL
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                accion TEXT NOT NULL,
                archivo TEXT,
                fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
            """)
            conn.commit()
            print("✅ Tablas creadas o ya existentes.")
    except sqlite3.Error as e:
        print(f"❌ Error al crear las tablas: {e}")


def insertar_usuario(username, password, permisos="lectura"):
    """Inserta un nuevo usuario en la base de datos, si no existe."""
    password_hash = sha256(password.encode()).hexdigest()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Verificar si el usuario ya existe
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"⚠ El usuario '{username}' ya existe.")
                return False

            # Insertar usuario
            cursor.execute("""
            INSERT INTO usuarios (username, password, permisos)
            VALUES (?, ?, ?)
            """, (username, password_hash, permisos))
            conn.commit()
            print(f"✅ Usuario '{username}' creado correctamente con permisos: {permisos}")
            return True
    except sqlite3.Error as e:
        print(f"❌ Error al insertar usuario: {e}")
        return False


def registrar_usuario(username, password, permisos="lectura"):
    """Registra un nuevo usuario con permisos predeterminados."""
    password_hash = sha256(password.encode()).hexdigest()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Verificar si el usuario ya existe
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            if cursor.fetchone():
                return f"❌ Error: El usuario '{username}' ya existe."

            # Insertar el nuevo usuario
            cursor.execute("""
            INSERT INTO usuarios (username, password, permisos)
            VALUES (?, ?, ?)
            """, (username, password_hash, permisos))
            conn.commit()
            return f"✅ Usuario '{username}' registrado con permisos: {permisos}"
    except sqlite3.Error as e:
        return f"❌ Error al registrar usuario: {e}"

def autenticar_usuario(username, password):
    """Autentica un usuario verificando su contraseña."""
    password_hash = sha256(password.encode()).hexdigest()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, permisos FROM usuarios WHERE username = ? AND password = ?
            """, (username, password_hash))
            return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"❌ Error al autenticar usuario: {e}")
        return None

def eliminar_usuario(username):
    """Elimina un usuario de la base de datos."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
            conn.commit()
            print(f"✅ Usuario '{username}' eliminado correctamente.")
    except sqlite3.Error as e:
        print(f"❌ Error al eliminar usuario: {e}")

def registrar_log(usuario_id, accion, archivo=None):
    """Registra una acción en los logs."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO logs (usuario_id, accion, archivo)
            VALUES (?, ?, ?)
            """, (usuario_id, accion, archivo))
            conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Error al registrar log: {e}")

def listar_usuarios():
    """Muestra todos los usuarios registrados en la base de datos."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, permisos FROM usuarios")
            usuarios = cursor.fetchall()

        if usuarios:
            print("\n👥 Usuarios registrados:")
            for usuario in usuarios:
                print(f"🆔 ID: {usuario[0]} | 👤 Usuario: {usuario[1]} | 🔑 Permisos: {usuario[2]}")
        else:
            print("\n🚫 No hay usuarios en la base de datos.")
    except sqlite3.Error as e:
        print(f"❌ Error al listar usuarios: {e}")

if __name__ == "__main__":
    print("📂 Creando tablas si no existen...")
    crear_tablas()

    print("\n👥 Usuarios registrados en la base de datos:")
    listar_usuarios()
