import os
import time
import logging
from .celery_app import app
from base_datos.db import registrar_log

# Configurar logging
logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3)
def procesar_archivo(self, ruta_archivo, usuario_id, operacion):
    """
    Tarea para procesar un archivo de forma asíncrona.
    
    Args:
        ruta_archivo (str): Ruta del archivo a procesar
        usuario_id (int): ID del usuario que solicitó la operación
        operacion (str): Tipo de operación (COMPRIMIR, CIFRAR, etc.)
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        logger.info(f"Iniciando procesamiento de archivo: {ruta_archivo}")
        
        # Simulamos una operación que toma tiempo
        time.sleep(2)
        
        # Registramos la operación en los logs
        registrar_log(usuario_id, f"{operacion}_ASYNC", os.path.basename(ruta_archivo))
        
        return {
            "estado": "completado",
            "archivo": os.path.basename(ruta_archivo),
            "operacion": operacion
        }
    except Exception as e:
        logger.error(f"Error al procesar archivo {ruta_archivo}: {e}")
        # Reintentamos la tarea en caso de error
        self.retry(exc=e, countdown=5)  # Reintento en 5 segundos

@app.task
def comprimir_archivo_async(ruta_archivo, usuario_id):
    """
    Tarea para comprimir un archivo de forma asíncrona.
    
    Args:
        ruta_archivo (str): Ruta del archivo a comprimir
        usuario_id (int): ID del usuario que solicitó la compresión
    
    Returns:
        dict: Resultado de la operación
    """
    import zipfile
    
    try:
        nombre_archivo = os.path.basename(ruta_archivo)
        directorio = os.path.dirname(ruta_archivo)
        archivo_zip = os.path.join(directorio, f"{nombre_archivo}.zip")
        
        # Crear archivo ZIP
        with zipfile.ZipFile(archivo_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(ruta_archivo, nombre_archivo)
        
        # Registrar en logs
        registrar_log(usuario_id, "COMPRIMIR_ASYNC", nombre_archivo)
        
        return {
            "estado": "completado",
            "archivo_original": nombre_archivo,
            "archivo_comprimido": f"{nombre_archivo}.zip"
        }
    except Exception as e:
        logger.error(f"Error al comprimir archivo {ruta_archivo}: {e}")
        return {
            "estado": "error",
            "mensaje": str(e)
        }

@app.task
def cifrar_archivo_async(ruta_archivo, usuario_id, clave):
    """
    Tarea para cifrar un archivo de forma asíncrona.
    
    Args:
        ruta_archivo (str): Ruta del archivo a cifrar
        usuario_id (int): ID del usuario que solicitó el cifrado
        clave (str): Clave para cifrar el archivo
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        from cryptography.fernet import Fernet
        import base64
        import hashlib
        
        # Generar clave de cifrado a partir de la clave proporcionada
        clave_bytes = clave.encode()
        clave_hash = hashlib.sha256(clave_bytes).digest()
        clave_base64 = base64.urlsafe_b64encode(clave_hash)
        
        # Crear objeto Fernet para cifrado
        fernet = Fernet(clave_base64)
        
        # Leer archivo
        with open(ruta_archivo, 'rb') as file:
            contenido = file.read()
        
        # Cifrar contenido
        contenido_cifrado = fernet.encrypt(contenido)
        
        # Guardar archivo cifrado
        archivo_cifrado = f"{ruta_archivo}.enc"
        with open(archivo_cifrado, 'wb') as file:
            file.write(contenido_cifrado)
        
        # Registrar en logs
        registrar_log(usuario_id, "CIFRAR_ASYNC", os.path.basename(ruta_archivo))
        
        return {
            "estado": "completado",
            "archivo_original": os.path.basename(ruta_archivo),
            "archivo_cifrado": os.path.basename(archivo_cifrado)
        }
    except Exception as e:
        logger.error(f"Error al cifrar archivo {ruta_archivo}: {e}")
        return {
            "estado": "error",
            "mensaje": str(e)
        }