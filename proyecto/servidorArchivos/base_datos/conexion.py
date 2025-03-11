import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Subir un nivel
DB_PATH = os.path.join(BASE_DIR, "base_datos", "servidor_archivos.db")

def obtener_conexion():
    """Devuelve una conexión a la base de datos."""
    return sqlite3.connect(DB_PATH)
