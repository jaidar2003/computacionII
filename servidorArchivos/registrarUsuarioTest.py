import sqlite3
import bcrypt
import os

# Ruta absoluta segura desde el directorio actual
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'base_datos'))
DB_PATH = os.path.join(BASE_DIR, 'servidor_archivos.db')

def registrar_usuario_test():
    try:
        if not os.path.exists(DB_PATH):
            print(f"\u274c La base de datos no existe en: {DB_PATH}")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Eliminar usuario si ya existe
        cursor.execute("DELETE FROM usuarios WHERE username = ?", ("testuser",))
        conn.commit()
        print("🧹 Usuario 'testuser' eliminado (si existía).")

        # Insertar nuevo usuario
        hashed = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO usuarios (username, password, permisos) VALUES (?, ?, ?)",
            ("testuser", hashed.decode('utf-8'), "lectura")
        )
        conn.commit()
        print("\u2705 Usuario 'testuser' registrado correctamente con contraseña válida.")
        conn.close()

    except Exception as e:
        print(f"\u274c Error al registrar usuario: {e}")

if __name__ == '__main__':
    registrar_usuario_test()
