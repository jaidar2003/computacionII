import os
import sqlite3
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# 🔌 Conexión y configuración
# ---------------------------

def obtener_conexion():
    """
    Retorna una conexión a la base de datos.
    Usa DB_PATH de entorno o una ruta por defecto.
    """
    db_path = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'servidor_archivos.db'))
    return sqlite3.connect(db_path)

# ---------------------------
# 🛠️ Crear tablas
# ---------------------------

def crear_tablas():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            permisos TEXT DEFAULT 'lectura'
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            accion TEXT NOT NULL,
            archivo TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            ip TEXT,
            accion TEXT,
            mensaje TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

        print("✅ Tablas creadas o ya existentes.")
        return True
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return False

# ---------------------------
# 👤 Registro y autenticación
# ---------------------------

def registrar_usuario(username, password, permisos='lectura'):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return "❌ Usuario ya existente."

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO usuarios (username, password, permisos) VALUES (?, ?, ?)",
            (username, hashed.decode('utf-8'), permisos)
        )
        conn.commit()
        conn.close()

        return "✅ Usuario registrado exitosamente."
    except Exception as e:
        return f"❌ Error al registrar usuario: {e}"

def autenticar_usuario(username, password):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, permisos FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            return (user[0], user[2])  # Retorna ID y permisos
        return None
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return None

# ---------------------------
# 📝 Registro de logs
# ---------------------------

def registrar_log(usuario_id, accion, archivo=None):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (usuario_id, accion, archivo) VALUES (?, ?, ?)",
            (usuario_id, accion, archivo)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error al registrar log: {e}")
        return False

def log_evento(usuario, ip, accion, mensaje):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO log_eventos (usuario, ip, accion, mensaje, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario, ip, accion, mensaje, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] No se pudo registrar el log_evento: {e}")
