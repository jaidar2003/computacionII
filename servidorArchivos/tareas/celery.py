import hashlib
import subprocess
import os
from celery import Celery
from dotenv import load_dotenv
from base_datos.db import log_evento

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/0")

app = Celery(
    'verificador_archivos',
    broker='redis://localhost:6379/0',   # Asegurate de tener Redis corriendo
    backend='rpc://'
)


@app.task
def verificar_integridad_y_virus(ruta_archivo, hash_esperado=None):
    """
    Tarea Celery para verificar que un archivo no esté corrupto y no tenga virus.
    - Comprueba el hash SHA-256 si se proporciona uno.
    - Ejecuta clamscan para escanear el archivo.
    También registra el resultado en la base de datos.
    """
    resultado = {
        'ruta': ruta_archivo,
        'estado': 'desconocido',
        'integridad': 'no verificada',
        'virus': 'no escaneado',
        'mensaje': ''
    }

    # Verificar integridad (hash)
    if hash_esperado:
        try:
            with open(ruta_archivo, 'rb') as f:
                contenido = f.read()
                hash_actual = hashlib.sha256(contenido).hexdigest()
                if hash_actual == hash_esperado:
                    resultado['integridad'] = 'válida'
                else:
                    resultado['integridad'] = 'inválida'
                    resultado['estado'] = 'corrupto'
                    resultado['mensaje'] += 'Hash no coincide. '
        except Exception as e:
            resultado['integridad'] = 'error'
            resultado['mensaje'] += f"Error al calcular hash: {e}. "

    # Verificar virus con ClamAV
    try:
        escaneo = subprocess.run(['clamscan', ruta_archivo], capture_output=True, text=True)
        salida = escaneo.stdout
        if "Infected files: 0" in salida:
            resultado['virus'] = 'limpio'
        else:
            resultado['virus'] = 'infectado'
            resultado['estado'] = 'infectado'
            resultado['mensaje'] += 'Archivo infectado. '
    except FileNotFoundError:
        resultado['virus'] = 'error'
        resultado['mensaje'] += 'ClamAV no encontrado. '
    except Exception as e:
        resultado['virus'] = 'error'
        resultado['mensaje'] += f"Error en escaneo: {e}. "

    if resultado['estado'] == 'desconocido':
        resultado['estado'] = 'ok'
        resultado['mensaje'] = 'Archivo verificado con éxito.'

    # Guardar en log_eventos
    try:
        log_evento("celery", "localhost", "VERIFICACION", f"{resultado['estado'].upper()} - {resultado['mensaje']}")
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el resultado en log_eventos: {e}")

    return resultado
