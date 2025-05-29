import os
import hashlib
import getpass

def input_password(prompt="Contraseña: "):
    try:
        return getpass.getpass(prompt)
    except Exception as e:
        print("⚠️ Error al ocultar la contraseña, se usará input normal.")
        return input(prompt)

def calcular_hash_archivo(ruta_archivo):
    """
    Calcula el hash SHA-256 de un archivo.

    Args:
        ruta_archivo (str): Ruta al archivo

    Returns:
        str: Hash SHA-256 en hexadecimal o None si falla
    """
    try:
        with open(ruta_archivo, 'rb') as f:
            contenido = f.read()
            return hashlib.sha256(contenido).hexdigest()
    except Exception as e:
        print(f"❌ Error al calcular hash: {e}")
        return None
