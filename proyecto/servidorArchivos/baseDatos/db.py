import os
import sqlite3
from hashlib import sha256

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Subimos un nivel
DB_PATH = os.path.join(BASE_DIR, 'baseDatos', 'servidor_archivos.db')

# Asegurarse de que la carpeta 'baseDatos' exista
if not os.path.exists(os.path.dirname(DB_PATH)):
    os.makedirs(os.path.dirname(DB_PATH))

def crear_tablas():
    """Crea las tablas necesarias si no existen."""
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



def registrar_usuario(username, password, permisos="lectura"):
    """Registra un nuevo usuario con permisos predeterminados."""
    password_hash = sha256(password.encode()).hexdigest()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            return f"Error: El usuario '{username}' ya existe."

        # Insertar el nuevo usuario
        cursor.execute("""
        INSERT INTO usuarios (username, password, permisos)
        VALUES (?, ?, ?)
        """, (username, password_hash, permisos))
        conn.commit()

    return f"Usuario '{username}' registrado exitosamente con permisos: {permisos}"


def insertar_usuario(username, password, permisos):
    """Inserta un nuevo usuario si no existe en la base de datos."""
    password_hash = sha256(password.encode()).hexdigest()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"El usuario '{username}' ya existe en la base de datos.")
            return  # Salir sin insertar de nuevo

        # Insertar usuario si no existe
        cursor.execute("""
        INSERT INTO usuarios (username, password, permisos)
        VALUES (?, ?, ?)
        """, (username, password_hash, permisos))
        conn.commit()

        print(f"Usuario '{username}' creado correctamente.")


def autenticar_usuario(username, password):
    """Autentica un usuario verificando su contraseña."""
    password_hash = sha256(password.encode()).hexdigest()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, permisos FROM usuarios WHERE username = ? AND password = ?
        """, (username, password_hash))
        return cursor.fetchone()


def eliminar_usuario(username):
    """Elimina un usuario de la base de datos."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
        conn.commit()
        print(f"Usuario '{username}' eliminado correctamente.")


def tiene_permiso(usuario_id, permiso_requerido):
    """Verifica si el usuario tiene el permiso solicitado."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
        resultado = cursor.fetchone()

    if resultado:
        permisos = resultado[0].split(",")  # Convertir string en lista
        return permiso_requerido in permisos or "admin" in permisos  # Admin tiene acceso a todo

    return False  # Usuario no encontrado


def registrar_log(usuario_id, accion, archivo=None):
    """Registra una acción en los logs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO logs (usuario_id, accion, archivo)
        VALUES (?, ?, ?)
        """, (usuario_id, accion, archivo))
        conn.commit()


def listar_usuarios():
    """Muestra todos los usuarios registrados en la base de datos."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, permisos FROM usuarios")
        usuarios = cursor.fetchall()

    if usuarios:
        print("Usuarios registrados:")
        for usuario in usuarios:
            print(f"ID: {usuario[0]}, Usuario: {usuario[1]}, Permisos: {usuario[2]}")
    else:
        print("No hay usuarios en la base de datos.")


