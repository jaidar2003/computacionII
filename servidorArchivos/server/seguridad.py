"""
🔐 Módulo de Seguridad del Servidor de Archivos
----------------------------------------------
Este módulo implementa las funciones de seguridad para el servidor,
incluyendo autenticación de usuarios, registro y gestión de contraseñas.

Características principales:
- 🔑 Autenticación de usuarios contra la base de datos
- 👤 Registro de nuevos usuarios
- 🔒 Generación segura de hashes de contraseñas
- ✅ Verificación de contraseñas
- 🛡️ Implementación alternativa cuando bcrypt no está disponible

El módulo utiliza bcrypt para el hash de contraseñas cuando está disponible,
o una implementación básica con hashlib y salt cuando no lo está.
"""

import os
import sys
import hashlib
import base64
import logging

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from base_datos.db import autenticar_usuario, registrar_usuario as db_registrar_usuario

# 🔄 Configuración de logging
logger = logging.getLogger(__name__)

# 🔒 Constantes para seguridad
SALT_BYTES = 16  # Tamaño del salt en bytes
HASH_SEPARATOR = '$'  # Separador entre salt y hash

# 🛡️ Intenta importar bcrypt, si no está disponible, usa una implementación básica con hashlib
try:
    import bcrypt
    USING_BCRYPT = True
    logger.info("✅ Usando bcrypt para el hash de contraseñas.")
    print("✅ Usando bcrypt para el hash de contraseñas.")
except ImportError:
    USING_BCRYPT = False
    logger.warning("⚠️ bcrypt no está instalado. Usando implementación básica para el hash de contraseñas.")
    print("⚠️ bcrypt no está instalado. Usando implementación básica para el hash de contraseñas.")

def autenticar_usuario_en_servidor(username, password):
    """
    🔑 Autentica un usuario contra la base de datos.

    Args:
        username (str): Nombre de usuario
        password (str): Contraseña en texto plano

    Returns:
        tuple: (id, permisos) si la autenticación es exitosa, None en caso contrario
    """
    try:
        usuario = autenticar_usuario(username, password)
        if usuario:
            logger.info(f"✅ Usuario {username} autenticado correctamente")
            return usuario  # Devuelve (id, permisos)

        logger.warning(f"❌ Intento de autenticación fallido para el usuario {username}")
        return None
    except Exception as error:
        logger.error(f"❌ Error durante la autenticación del usuario {username}: {error}")
        return None

def registrar_usuario(username, password, permisos="lectura"):
    """
    👤 Registra un nuevo usuario en la base de datos.

    Args:
        username (str): Nombre de usuario
        password (str): Contraseña en texto plano
        permisos (str, optional): Nivel de permisos. Defaults to "lectura".

    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    try:
        resultado = db_registrar_usuario(username, password, permisos)
        if resultado.startswith("✅"):
            logger.info(f"✅ Usuario {username} registrado correctamente con permisos de {permisos}")
        else:
            logger.warning(f"⚠️ No se pudo registrar al usuario {username}: {resultado}")
        return resultado
    except Exception as error:
        mensaje_error = f"❌ Error al registrar usuario {username}: {error}"
        logger.error(mensaje_error)
        return mensaje_error

def hash_password(password: str) -> str:
    """
    🔒 Genera un hash seguro para la contraseña.

    Utiliza bcrypt si está disponible, o una implementación básica 
    con hashlib y salt si no lo está.

    Args:
        password (str): Contraseña en texto plano

    Returns:
        str: Hash de la contraseña

    Raises:
        ValueError: Si la contraseña está vacía
    """
    if not password:
        raise ValueError("❌ La contraseña no puede estar vacía")

    try:
        if USING_BCRYPT:
            # 🛡️ Usar bcrypt (más seguro)
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            # 🔧 Implementación básica con hashlib y salt
            return _hash_password_basic(password)
    except Exception as error:
        logger.error(f"❌ Error al generar hash de contraseña: {error}")
        raise

def _hash_password_basic(password: str) -> str:
    """
    🔧 Implementación básica de hash con hashlib y salt.

    Args:
        password (str): Contraseña en texto plano

    Returns:
        str: Hash de la contraseña en formato "salt$hash"
    """
    # Generar salt aleatorio
    salt = base64.b64encode(os.urandom(SALT_BYTES)).decode('utf-8')

    # Calcular hash
    h = hashlib.sha256()
    h.update((password + salt).encode('utf-8'))

    # Devolver en formato "salt$hash"
    return f"{salt}{HASH_SEPARATOR}{h.hexdigest()}"

def verificar_password(password: str, hashed: str) -> bool:
    """
    ✅ Verifica si una contraseña coincide con su hash.

    Utiliza bcrypt si está disponible, o una implementación básica
    con hashlib y salt si no lo está.

    Args:
        password (str): Contraseña en texto plano
        hashed (str): Hash almacenado

    Returns:
        bool: True si la contraseña coincide, False en caso contrario
    """
    if not password or not hashed:
        return False

    try:
        if USING_BCRYPT:
            # 🛡️ Usar bcrypt (más seguro)
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        else:
            # 🔧 Implementación básica con hashlib y salt
            return _verificar_password_basic(password, hashed)
    except Exception as error:
        logger.error(f"❌ Error al verificar contraseña: {error}")
        return False

def _verificar_password_basic(password: str, hashed: str) -> bool:
    """
    🔧 Implementación básica de verificación de contraseña con hashlib y salt.

    Args:
        password (str): Contraseña en texto plano
        hashed (str): Hash almacenado en formato "salt$hash"

    Returns:
        bool: True si la contraseña coincide, False en caso contrario
    """
    try:
        # Separar salt y hash
        salt, hash_value = hashed.split(HASH_SEPARATOR, 1)

        # Calcular hash con la contraseña proporcionada y el salt almacenado
        h = hashlib.sha256()
        h.update((password + salt).encode('utf-8'))

        # Comparar hashes
        return h.hexdigest() == hash_value
    except Exception as error:
        logger.debug(f"❌ Error en verificación básica de contraseña: {error}")
        return False

# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo seguridad.py cargado correctamente.")
    print("✅ Importación de base_datos.db exitosa.")

    # Prueba simple de las funciones
    print("🧪 Probando funciones de hash y verificación...")
    test_password = "contraseña_segura"
    hashed = hash_password(test_password)
    print(f"🔒 Hash generado: {hashed}")
    verificacion = verificar_password(test_password, hashed)
    print(f"✅ Verificación correcta: {verificacion}")
