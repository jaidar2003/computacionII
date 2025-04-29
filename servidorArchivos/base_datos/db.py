import os
import sqlite3
from hashlib import sha256

# Definir la ruta de la base de datos
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Subir un nivel
DB_PATH = os.path.join(BASE_DIR, "base_datos", "servidor_archivos.db")

# Asegurar que la carpeta exista
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH))

def obtener_conexion():
    return sqlite3.connect(DB_PATH)


def registrar_log(usuario_id, accion, archivo=None):
    """Registra una acción en los logs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO logs (usuario_id, accion, archivo)
        VALUES (?, ?, ?)
        """, (usuario_id, accion, archivo))
        conn.commit()

def registrar_usuario(username, password, permisos="lectura"):
    """Registra un nuevo usuario en la base de datos."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO usuarios (username, password, permisos)
            VALUES (?, ?, ?)
            """, (username, password, permisos))
            conn.commit()
            return "✅ Usuario registrado exitosamente."
    except sqlite3.Error as e:
        return f"❌ Error al registrar usuario: {e}"

def crear_tablas():
    """Crea las tablas necesarias si no existen."""
    try:
        with obtener_conexion() as conn:
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

def autenticar_usuario(username, password):
    """Autentica un usuario verificando su contraseña."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, permisos FROM usuarios WHERE username = ? AND password = ?
            """, (username, password))
            return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"❌ Error al autenticar usuario: {e}")
        return None
