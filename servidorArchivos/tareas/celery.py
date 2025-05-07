import hashlib
import subprocess
import os
from celery import Celery
from dotenv import load_dotenv
from base_datos.db import log_evento

# 🧪 Carga las variables de entorno desde .env
load_dotenv()

# 📍 Configuración de la URL del broker y backend (Redis por defecto)
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")  # Cola de tareas
BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/0")  # Resultado de tareas

# 🚀 Inicializa la app Celery
app = Celery(
    'verificador_archivos',
    broker=BROKER_URL,  # Redis actúa como cola de mensajes
    backend='rpc://'  # Para retornar resultados desde el worker
)


@app.task
def verificar_integridad_y_virus(ruta_archivo, hash_esperado=None):
    """
    Esta tarea se ejecuta en segundo plano usando Celery y Redis como broker.

    Funcionalidades:
    1. Verifica la integridad del archivo calculando el hash SHA-256.
    2. Ejecuta ClamAV (clamscan) para verificar si hay virus.
    3. Registra los resultados en la base de datos.
    """
    resultado = {
        'ruta': ruta_archivo,
        'estado': 'desconocido',
        'integridad': 'no verificada',
        'virus': 'no escaneado',
        'mensaje': ''
    }

    # ✅ Verificación de integridad (Hash SHA-256)
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

    # 🦠 Verificación de virus usando ClamAV
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

    # 🏁 Si todo salió bien y no hubo errores
    if resultado['estado'] == 'desconocido':
        resultado['estado'] = 'ok'
        resultado['mensaje'] = 'Archivo verificado con éxito.'

    # 📝 Registrar el evento en la base de datos (log_eventos)
    try:
        log_evento("celery", "localhost", "VERIFICACION", f"{resultado['estado'].upper()} - {resultado['mensaje']}")
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el resultado en log_eventos: {e}")

    return resultado
