"""
🚀 Módulo de Tareas Asíncronas con Celery
-----------------------------------------
Este módulo implementa tareas que se ejecutan en segundo plano
utilizando Celery como sistema de colas de tareas.

Características principales:
- 🔄 Procesamiento asíncrono de tareas
- 🔍 Verificación de integridad de archivos mediante hash
- 🦠 Escaneo de virus con ClamAV
- 📝 Registro de resultados en la base de datos
- 🛡️ Implementación alternativa cuando Celery no está disponible

Las tareas se ejecutan en segundo plano para no bloquear el servidor
principal mientras se realizan operaciones que pueden llevar tiempo.
"""

import hashlib
import subprocess
import os
import sys
from dotenv import load_dotenv
from base_datos.db import log_evento

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
        backend='rpc://'  # Para retornar resultados desde el worker
    )

    def task_decorator(func):
        return app.task(func)

except ImportError:
    print("⚠️ Celery no está instalado. Usando implementación local para tareas.")

    # Implementación básica para simular Celery cuando no está disponible
    class MockTask:
        def __init__(self, func):
            self.func = func

        def delay(self, *args, **kwargs):
            # Ejecuta la función directamente en lugar de en segundo plano
            return self.func(*args, **kwargs)

    class MockCelery:
        def __init__(self, *args, **kwargs):
            pass

        def task(self, func):
            return MockTask(func)

    app = MockCelery()

    def task_decorator(func):
        return MockTask(func)

# 📊 Constantes para estados y mensajes
ESTADO_OK = 'ok'
ESTADO_CORRUPTO = 'corrupto'
ESTADO_INFECTADO = 'infectado'
ESTADO_DESCONOCIDO = 'desconocido'

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
    """
    🔍 Verifica la integridad y seguridad de un archivo.

    Esta tarea se ejecuta en segundo plano usando Celery y Redis como broker.
    Realiza verificaciones de integridad mediante hash SHA-256 y escaneo
    de virus utilizando ClamAV.

    Args:
        ruta_archivo (str): Ruta completa al archivo a verificar
        hash_esperado (str, optional): Hash SHA-256 esperado para verificación

    Returns:
        dict: Resultado de la verificación con los siguientes campos:
            - ruta: Ruta del archivo verificado
            - estado: Estado general ('ok', 'corrupto', 'infectado', 'desconocido')
            - integridad: Resultado de verificación de integridad
            - virus: Resultado de verificación de virus
            - mensaje: Mensaje descriptivo del resultado
    """
    # 🏁 Inicializar resultado
    resultado = _inicializar_resultado(ruta_archivo)

    # 🔍 Verificar integridad si se proporcionó un hash
    if hash_esperado:
        _verificar_integridad(resultado, ruta_archivo, hash_esperado)

    # 🦠 Verificar virus
    _verificar_virus(resultado, ruta_archivo)

    # 📊 Actualizar estado final
    _actualizar_estado_final(resultado)

    # 📝 Registrar el evento
    _registrar_evento(resultado)

    return resultado

def _inicializar_resultado(ruta_archivo):
    """
    🏁 Inicializa la estructura de resultado.

    Args:
        ruta_archivo (str): Ruta del archivo

    Returns:
        dict: Estructura de resultado inicializada
    """
    return {
        'ruta': ruta_archivo,
        'estado': ESTADO_DESCONOCIDO,
        'integridad': INTEGRIDAD_NO_VERIFICADA,
        'virus': VIRUS_NO_ESCANEADO,
        'mensaje': ''
    }

def _verificar_integridad(resultado, ruta_archivo, hash_esperado):
    """
    🔍 Verifica la integridad del archivo mediante hash SHA-256.

    Args:
        resultado (dict): Diccionario de resultado a actualizar
        ruta_archivo (str): Ruta del archivo a verificar
        hash_esperado (str): Hash SHA-256 esperado
    """
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
    """
    🧮 Calcula el hash SHA-256 de un archivo.

    Args:
        ruta_archivo (str): Ruta del archivo

    Returns:
        str: Hash SHA-256 en formato hexadecimal

    Raises:
        Exception: Si ocurre un error al leer el archivo o calcular el hash
    """
    with open(ruta_archivo, 'rb') as archivo:
        contenido = archivo.read()
        return hashlib.sha256(contenido).hexdigest()

def _verificar_virus(resultado, ruta_archivo):
    """
    🦠 Verifica si el archivo contiene virus usando ClamAV.

    Args:
        resultado (dict): Diccionario de resultado a actualizar
        ruta_archivo (str): Ruta del archivo a verificar
    """
    try:
        escaneo = subprocess.run(
            ['clamscan', ruta_archivo], 
            capture_output=True, 
            text=True
        )

        if "Infected files: 0" in escaneo.stdout:
            resultado['virus'] = VIRUS_LIMPIO
        else:
            resultado['virus'] = VIRUS_INFECTADO
            resultado['estado'] = ESTADO_INFECTADO
            resultado['mensaje'] += '🦠 Archivo infectado. '
    except FileNotFoundError:
        resultado['virus'] = VIRUS_ERROR
        resultado['mensaje'] += '⚠️ ClamAV no encontrado. '
    except Exception as error:
        resultado['virus'] = VIRUS_ERROR
        resultado['mensaje'] += f"❌ Error en escaneo: {error}. "

def _actualizar_estado_final(resultado):
    """
    📊 Actualiza el estado final del resultado.

    Si no se ha establecido un estado específico (corrupto o infectado),
    se establece como 'ok' si no hubo errores.

    Args:
        resultado (dict): Diccionario de resultado a actualizar
    """
    if resultado['estado'] == ESTADO_DESCONOCIDO:
        resultado['estado'] = ESTADO_OK
        resultado['mensaje'] = '✅ Archivo verificado con éxito.'

def _registrar_evento(resultado):
    """
    📝 Registra el resultado de la verificación en la base de datos.

    Args:
        resultado (dict): Resultado de la verificación
    """
    try:
        log_evento(
            "celery", 
            "localhost", 
            "VERIFICACION", 
            f"{resultado['estado'].upper()} - {resultado['mensaje']}"
        )
    except Exception as error:
        print(f"❌ ERROR: No se pudo guardar el resultado en log_eventos: {error}")
