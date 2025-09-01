import os
import json
import functools
from .config import SESSION_FILE

def save_session(session_data):
    """Guardar datos de sesión en un archivo"""
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f)

def load_session():
    """Cargar datos de sesión desde un archivo"""
    if not os.path.exists(SESSION_FILE):
        return None
    
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def clear_session():
    """Eliminar archivo de sesión"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def check_auth(func):
    """Decorador para verificar si hay una sesión activa"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = load_session()
        if not session:
            print("❌ Debes iniciar sesión primero. Usa el comando 'login'")
            return
        return func(*args, **kwargs)
    return wrapper