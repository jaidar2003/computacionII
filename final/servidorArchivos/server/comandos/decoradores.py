
import os
import sys
from functools import wraps

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from baseDeDatos.db import obtener_conexion

# Niveles de permisos en orden jerárquico
NIVELES_PERMISOS = {
    'lectura': 1,
    'escritura': 2,
    'admin': 3
}

# Decorador para validar argumentos
def validar_argumentos(num_args=None, min_args=None, max_args=None, mensaje_error=None):
    def decorador(func):
        @wraps(func)
        def wrapper(partes, *args, **kwargs):
            # Restar 1 para no contar el comando mismo
            num_argumentos = len(partes) - 1

            if num_args is not None and num_argumentos != num_args:
                return mensaje_error or f"❌ Este comando requiere exactamente {num_args} argumento(s)."

            if min_args is not None and num_argumentos < min_args:
                return mensaje_error or f"❌ Este comando requiere al menos {min_args} argumento(s)."

            if max_args is not None and num_argumentos > max_args:
                return mensaje_error or f"❌ Este comando permite máximo {max_args} argumento(s)."

            return func(partes, *args, **kwargs)
        return wrapper
    return decorador

# Función para verificar si un usuario tiene un nivel de permiso específico
def _tiene_permiso(usuario_id, nivel_requerido):
    if not usuario_id:
        return False

    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Obtener permisos del usuario
        from .permisos import _obtener_permisos_usuario
        permisos_usuario = _obtener_permisos_usuario(cursor, usuario_id)
        conn.close()

        if not permisos_usuario:
            return False

        # Verificar si el nivel de permiso del usuario es suficiente
        nivel_usuario = NIVELES_PERMISOS.get(permisos_usuario, 0)
        nivel_necesario = NIVELES_PERMISOS.get(nivel_requerido, 0)

        return nivel_usuario >= nivel_necesario

    except Exception as error:
        print(f"❌ Error al verificar permisos: {error}")
        return False

# Decorador para verificar permisos
def requiere_permiso(nivel_requerido):
    def decorador(func):
        @wraps(func)
        def wrapper(partes, directorio_base, usuario_id=None, *args, **kwargs):
            # Verificar permisos
            if not _tiene_permiso(usuario_id, nivel_requerido):
                return f"❌ No tienes permisos suficientes. Se requiere nivel: {nivel_requerido}"

            # Si tiene permisos, ejecutar la función
            return func(partes, directorio_base, usuario_id, *args, **kwargs)
        return wrapper
    return decorador
