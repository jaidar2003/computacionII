import os
import sys
import logging

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from baseDeDatos.db import autenticar_usuario, registrar_usuario as db_registrar_usuario

# 🔄 Configuración de logging
logger = logging.getLogger(__name__)


import bcrypt
logger.info("✅ bcrypt habilitado para el hash de contraseñas.")

def autenticar_usuario_en_servidor(username, password):
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
    if not password:
        raise ValueError("❌ La contraseña no puede estar vacía")
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as error:
        logger.error(f"❌ Error al generar hash de contraseña: {error}")
        raise


def verificar_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as error:
        logger.error(f"❌ Error al verificar contraseña: {error}")
        return False


# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo seguridad.py cargado correctamente.")
    print("✅ Importación de baseDeDatos.db exitosa.")

    # Prueba simple de las funciones
    print("🧪 Probando funciones de hash y verificación...")
    test_password = "contraseña_segura"
    hashed = hash_password(test_password)
    print(f"🔒 Hash generado: {hashed}")
    verificacion = verificar_password(test_password, hashed)
    print(f"✅ Verificación correcta: {verificacion}")
