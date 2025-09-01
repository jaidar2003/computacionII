
import os
import sqlite3
import logging
from datetime import datetime
from dotenv import load_dotenv

# 📦 Cargar variables de entorno
load_dotenv()

# 🔄 Configuración de logging
logger = logging.getLogger(__name__)

# 🔧 Constantes para la base de datos
DEFAULT_DB_FILENAME = 'servidor_archivos.db'

# 📋 Definiciones de tablas
TABLA_USUARIOS = '''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    permisos TEXT DEFAULT 'usuario'
)
'''

TABLA_LOGS = '''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    accion TEXT NOT NULL,
    archivo TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
'''

TABLA_LOG_EVENTOS = '''
CREATE TABLE IF NOT EXISTS log_eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    ip TEXT,
    accion TEXT,
    mensaje TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
'''

def obtener_conexion():
    db_path = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), DEFAULT_DB_FILENAME))
    logger.debug(f"🔌 Conectando a la base de datos: {db_path}")
    return sqlite3.connect(db_path)

def crear_tablas():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Crear tabla de usuarios
        logger.debug("🗃️ Creando tabla de usuarios...")
        cursor.execute(TABLA_USUARIOS)

        # Crear tabla de logs
        logger.debug("🗃️ Creando tabla de logs...")
        cursor.execute(TABLA_LOGS)

        # Crear tabla de log_eventos
        logger.debug("🗃️ Creando tabla de log_eventos...")
        cursor.execute(TABLA_LOG_EVENTOS)

        conn.commit()
        conn.close()

        logger.info("✅ Tablas creadas o ya existentes.")
        print("✅ Tablas creadas o ya existentes.")
        return True
    except Exception as error:
        logger.error(f"❌ Error al crear tablas: {error}")
        print(f"❌ Error al crear tablas: {error}")
        return False

# Las funciones de seguridad se importarán dentro de las funciones que las necesiten
# para evitar importaciones circulares

def registrar_usuario(username, password, permisos='usuario'):
    if not username or not password:
        return "❌ El nombre de usuario y la contraseña son obligatorios."

    try:
        # 🔌 Obtener conexión y verificar si el usuario ya existe
        conn = obtener_conexion()
        cursor = conn.cursor()

        if _usuario_existe(cursor, username):
            conn.close()
            logger.warning(f"👤 Intento de registro de usuario existente: {username}")
            return "❌ Usuario ya existente."

        # 🔒 Generar hash de la contraseña
        try:
            # Importar hash_password en tiempo de ejecución para evitar importación circular
            from server.seguridad import hash_password
            hashed = hash_password(password)
        except Exception as error:
            conn.close()
            logger.error(f"🔒 Error al generar hash de contraseña: {error}")
            return f"❌ Error al procesar la contraseña: {error}"

        # 📝 Insertar el nuevo usuario
        cursor.execute(
            "INSERT INTO usuarios (username, password, permisos) VALUES (?, ?, ?)",
            (username, hashed, permisos)
        )

        conn.commit()
        conn.close()

        logger.info(f"✅ Usuario {username} registrado con permisos de {permisos}")
        return "✅ Usuario registrado exitosamente."
    except Exception as error:
        logger.error(f"❌ Error al registrar usuario {username}: {error}")
        return f"❌ Error al registrar usuario: {error}"

def _usuario_existe(cursor, username):
    cursor.execute("SELECT username FROM usuarios WHERE username = ?", (username,))
    return cursor.fetchone() is not None

def autenticar_usuario(username, password):
    if not username or not password:
        logger.warning("🔑 Intento de autenticación con credenciales vacías")
        return None

    try:
        # 🔌 Obtener conexión y buscar el usuario
        conn = obtener_conexion()
        cursor = conn.cursor()

        cursor.execute("SELECT id, password, permisos FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # 🔒 Verificar la contraseña
        # Importar verificar_password en tiempo de ejecución para evitar importación circular
        from server.seguridad import verificar_password
        if user and verificar_password(password, user[1]):
            return (user[0], user[2])  # (id, permisos)

        logger.warning(f"❌ Intento de autenticación fallido para el usuario {username}")
        return None
    except Exception as error:
        logger.error(f"❌ Error en autenticación de {username}: {error}")
        return None

def registrar_log(usuario_id, accion, archivo=None):
    try:
        # 🔌 Obtener conexión y registrar el log
        conn = obtener_conexion()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO logs (usuario_id, accion, archivo) VALUES (?, ?, ?)",
            (usuario_id, accion, archivo)
        )

        conn.commit()
        conn.close()

        logger.debug(f"📝 Log registrado: Usuario {usuario_id}, Acción: {accion}, Archivo: {archivo}")
        return True
    except Exception as error:
        logger.error(f"❌ Error al registrar log: {error}")
        return False

def log_evento(usuario, ip, accion, mensaje):
    try:
        # 🔌 Obtener conexión y registrar el evento
        conn = obtener_conexion()
        cursor = conn.cursor()

        fecha_actual = datetime.now()

        cursor.execute("""
            INSERT INTO log_eventos (usuario, ip, accion, mensaje, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario, ip, accion, mensaje, fecha_actual))

        conn.commit()
        conn.close()

        logger.debug(f"📊 Evento registrado: {accion} por {usuario} desde {ip}: {mensaje}")
    except Exception as error:
        logger.error(f"❌ Error al registrar evento: {error}")
        print(f"❌ No se pudo registrar el log_evento: {error}")
