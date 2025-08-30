import hashlib
import subprocess
import os
import sys
from dotenv import load_dotenv
from baseDeDatos.db import log_evento

# 🧪 Carga las variables de entorno desde .env
load_dotenv()

# Intenta importar Celery, si no está disponible, crea una implementación básica
try:
    from celery import Celery

    # 📍 Configuración de la URL del broker y backend (Redis por defecto)
    BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")  # Cola de tareas
    BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/0")  # Resultado de tareas

    # 🚀 Inicializa la app Celery
    app = Celery(
        'verificador_archivos',
        broker=BROKER_URL,  # Redis actúa como cola de mensajes
        backend=BACKEND_URL  # Backend para resultados (usar Redis por defecto)
    )

    def task_decorator(func):
        return app.task(func)

except ImportError:
    print("⚠️ Celery no está instalado. Las tareas se ejecutarán de forma síncrona.")

    # Decorador que permite invocar la función de manera directa y mediante .delay
    def task_decorator(func):
        def sync_call(*args, **kwargs):
            return func(*args, **kwargs)
        def delay(*args, **kwargs):
            return func(*args, **kwargs)
        sync_call.delay = delay
        return sync_call

    # Definir app como None para indicar que Celery no está disponible
    app = None

# 📊 Constantes para estados y mensajes
ESTADO_OK = 'ok'
ESTADO_CORRUPTO = 'corrupto'
ESTADO_INFECTADO = 'infectado'
ESTADO_DESCONOCIDO = 'desconocido'
ESTADO_PARCIAL = 'parcial'

INTEGRIDAD_VALIDA = 'válida'
INTEGRIDAD_INVALIDA = 'inválida'
INTEGRIDAD_ERROR = 'error'
INTEGRIDAD_NO_VERIFICADA = 'no verificada'

VIRUS_LIMPIO = 'limpio'
VIRUS_INFECTADO = 'infectado'
VIRUS_ERROR = 'error'
VIRUS_NO_ESCANEADO = 'no escaneado'

# Usar el decorador apropiado según si Celery está disponible o no
@task_decorator
def verificar_integridad_y_virus(ruta_archivo, hash_esperado=None):
    # Obtener solo el nombre del archivo sin la ruta completa
    nombre_archivo = os.path.basename(ruta_archivo)

    # 🏁 Mostrar mensaje de inicio
    print(f"✅ Iniciando verificación de '{nombre_archivo}' en segundo plano...")

    # 🏁 Inicializar resultado
    resultado = _inicializar_resultado(ruta_archivo)

    # Intentar cargar hash esperado desde archivo .hash si no se proporcionó
    if not hash_esperado:
        try:
            ruta_hash = f"{ruta_archivo}.hash"
            if os.path.exists(ruta_hash):
                with open(ruta_hash, 'r') as f:
                    hash_esperado = f.read().strip()
        except Exception as e:
            resultado['mensaje'] += f"⚠️ No se pudo leer hash esperado: {e}. "

    # 🔍 Verificar integridad si se tiene un hash esperado
    if hash_esperado:
        _verificar_integridad(resultado, ruta_archivo, hash_esperado)

    # 🦠 Verificar virus
    _verificar_virus(resultado, ruta_archivo)

    # 📊 Actualizar estado final
    _actualizar_estado_final(resultado)

    # 📝 Registrar el evento
    _registrar_evento(resultado)

    # 🏁 Mostrar mensaje de finalización
    print(f"✅ Verificación de '{nombre_archivo}' completada: {resultado['estado']} (Integridad: {resultado['integridad']}, Antivirus: {resultado['virus']})")

    return resultado

def _inicializar_resultado(ruta_archivo):
    return {
        'ruta': ruta_archivo,
        'estado': ESTADO_DESCONOCIDO,
        'integridad': INTEGRIDAD_NO_VERIFICADA,
        'virus': VIRUS_NO_ESCANEADO,
        'mensaje': ''
    }

def _verificar_integridad(resultado, ruta_archivo, hash_esperado):
    try:
        hash_actual = _calcular_hash_archivo(ruta_archivo)

        if hash_actual == hash_esperado:
            resultado['integridad'] = INTEGRIDAD_VALIDA
        else:
            resultado['integridad'] = INTEGRIDAD_INVALIDA
            resultado['estado'] = ESTADO_CORRUPTO
            resultado['mensaje'] += '❌ Hash no coincide. '
    except Exception as error:
        resultado['integridad'] = INTEGRIDAD_ERROR
        resultado['mensaje'] += f"❌ Error al calcular hash: {error}. "

def _calcular_hash_archivo(ruta_archivo):
    with open(ruta_archivo, 'rb') as archivo:
        contenido = archivo.read()
        return hashlib.sha256(contenido).hexdigest()

def _verificar_virus(resultado, ruta_archivo):
    try:
        escaneo = subprocess.run(
            ['clamscan', ruta_archivo],
            capture_output=True,
            text=True
        )

        # Códigos de salida de clamscan: 0 (sin virus), 1 (virus encontrado), 2 (error)
        if escaneo.returncode == 0:
            resultado['virus'] = VIRUS_LIMPIO
        elif escaneo.returncode == 1:
            resultado['virus'] = VIRUS_INFECTADO
            resultado['estado'] = ESTADO_INFECTADO
            resultado['mensaje'] += '🦠 Archivo infectado. '
        else:
            resultado['virus'] = VIRUS_ERROR
            resultado['mensaje'] += f"⚠️ Error en ClamAV (code {escaneo.returncode}). "
    except FileNotFoundError:
        resultado['virus'] = VIRUS_ERROR
        resultado['mensaje'] += '⚠️ ClamAV no encontrado. '
    except Exception as error:
        resultado['virus'] = VIRUS_ERROR
        resultado['mensaje'] += f"❌ Error en escaneo: {error}. "

def _actualizar_estado_final(resultado):
    if resultado['estado'] == ESTADO_DESCONOCIDO:
        # Si hubo errores en integridad o antivirus, marcar verificación parcial
        if resultado['integridad'] == INTEGRIDAD_ERROR or resultado['virus'] == VIRUS_ERROR:
            resultado['estado'] = ESTADO_PARCIAL
            if not resultado['mensaje']:
                resultado['mensaje'] = '⚠️ Verificación parcial por errores.'
        else:
            resultado['estado'] = ESTADO_OK
            if not resultado['mensaje']:
                resultado['mensaje'] = '✅ Archivo verificado con éxito.'

def _registrar_evento(resultado):
    try:
        # Obtener solo el nombre del archivo sin la ruta completa
        nombre_archivo = os.path.basename(resultado['ruta'])

        mensaje_detallado = (
            f"📄 {nombre_archivo}: {resultado['estado'].upper()} - "
            f"Integridad: {resultado['integridad']} - "
            f"Antivirus: {resultado['virus']} - "
            f"{resultado['mensaje']}"
        )

        log_evento(
            "celery", 
            "localhost", 
            "VERIFICACION", 
            mensaje_detallado
        )

        print(f"📝 Resultado guardado en la base de datos para '{nombre_archivo}'")
    except Exception as error:
        print(f"❌ ERROR: No se pudo guardar el resultado en log_eventos: {error}")
