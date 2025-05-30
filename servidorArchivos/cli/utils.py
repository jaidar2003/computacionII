"""
🛠️ Utilidades para el Cliente del Servidor de Archivos
----------------------------------------------------
Este módulo proporciona funciones de utilidad para el cliente,
como entrada segura de contraseñas y cálculo de hashes.

Funciones principales:
- 🔒 Entrada segura de contraseñas (ocultando la entrada)
- 🔍 Cálculo de hash SHA-256 para verificación de integridad
"""

import os
import hashlib
import getpass
import logging

# 🔄 Configuración de logging
logger = logging.getLogger(__name__)

def input_password(prompt="Contraseña: "):
    """
    🔒 Solicita una contraseña al usuario ocultando la entrada.

    Intenta determinar el mejor método para ocultar la entrada del usuario
    según el entorno. Suprime advertencias y utiliza fallbacks apropiados.

    Args:
        prompt (str, optional): Mensaje a mostrar al usuario. Defaults to "Contraseña: ".

    Returns:
        str: Contraseña ingresada por el usuario
    """
    import sys
    import io
    import warnings

    # Suprimir advertencias de getpass
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # Verificar si estamos en un entorno interactivo con terminal adecuado
        if sys.stdin.isatty() and hasattr(sys.stdin, 'fileno'):
            try:
                # Intentar usar getpass sin mostrar advertencias
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()  # Redirigir stderr para capturar advertencias
                password = getpass.getpass(prompt)
                sys.stderr = old_stderr  # Restaurar stderr
                return password
            except Exception as error:
                # Restaurar stderr si ocurrió una excepción
                sys.stderr = old_stderr
                logger.debug(f"⚠️ Error al usar getpass: {error}")
                # Continuar con el fallback

        # Fallback: usar input normal con mensaje de privacidad
        print("Ingrese su contraseña (los caracteres no se ocultarán):")
        return input(prompt)

def calcular_hash_archivo(ruta_archivo):
    """
    🔍 Calcula el hash SHA-256 de un archivo.

    Lee el archivo en modo binario y calcula su hash SHA-256,
    útil para verificar la integridad del archivo en el servidor.

    Args:
        ruta_archivo (str): Ruta al archivo a procesar

    Returns:
        str: Hash SHA-256 en formato hexadecimal o None si ocurre un error
    """
    if not os.path.exists(ruta_archivo):
        logger.error(f"❌ El archivo no existe: {ruta_archivo}")
        print(f"❌ El archivo no existe: {ruta_archivo}")
        return None

    if not os.path.isfile(ruta_archivo):
        logger.error(f"❌ La ruta no corresponde a un archivo: {ruta_archivo}")
        print(f"❌ La ruta no corresponde a un archivo: {ruta_archivo}")
        return None

    try:
        # Abrir archivo en modo binario y calcular hash
        with open(ruta_archivo, 'rb') as archivo:
            # Leer todo el contenido
            contenido = archivo.read()

            # Calcular hash SHA-256
            hash_resultado = hashlib.sha256(contenido).hexdigest()

            logger.debug(f"✅ Hash calculado para {ruta_archivo}: {hash_resultado[:8]}...")
            return hash_resultado

    except PermissionError:
        logger.error(f"❌ Sin permisos para leer el archivo: {ruta_archivo}")
        print(f"❌ Sin permisos para leer el archivo: {ruta_archivo}")
        return None
    except Exception as error:
        logger.error(f"❌ Error al calcular hash: {error}")
        print(f"❌ Error al calcular hash: {error}")
        return None
