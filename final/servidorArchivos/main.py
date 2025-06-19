import sys
import os
import argparse
import logging
import threading
import warnings
import subprocess
import ssl
from dotenv import load_dotenv

# 🛡️ Ignorar advertencias de deprecación
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 📚 Importaciones de módulos propios
from server.servidor import manejar_cliente
from baseDeDatos.db import crear_tablas
from cli.cliente import iniciar_cliente
from utils.config import verificar_configuracion_env, crear_directorio_si_no_existe, configurar_argumentos
from utils.config import CERT_PATH, KEY_PATH
from utils.network import crear_socket_servidor, configurar_contexto_ssl

# 📝 Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Verificar configuración del archivo .env
verificar_configuracion_env()

# ⚙️ Crear tablas si no existen
crear_tablas()

def iniciar_servidor_ssl(host=None, port=None, directorio=None):
    # Usar valores predeterminados si no se proporcionan
    host = host or os.getenv("SERVIDOR_HOST", "127.0.0.1")
    port = port or int(os.getenv("SERVIDOR_PORT", 1608))
    directorio = directorio or os.getenv("SERVIDOR_DIR", "archivos")
    # 📂 Asegurar que el directorio de archivos exista
    crear_directorio_si_no_existe(directorio)

    # 🔒 Configurar contexto SSL
    contexto = configurar_contexto_ssl(CERT_PATH, KEY_PATH)
    if not contexto:
        return

    try:
        # 🌐 Configurar socket
        socket_servidor = crear_socket_servidor(host, port)

        # 👂 Escuchar conexiones
        _escuchar_conexiones(socket_servidor, contexto, directorio)
    except Exception as error:
        logging.error(f"❌ Error al iniciar el servidor: {error}")

def _escuchar_conexiones(servidor, contexto, directorio):
    with servidor:
        while True:
            conexion, direccion = servidor.accept()
            try:
                conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
                # 🧵 Iniciar un hilo para manejar al cliente
                threading.Thread(target=manejar_cliente, 
                                args=(conexion_ssl, direccion, directorio)).start()
            except ssl.SSLError as error:
                logging.error(f"🔒 Error SSL con {direccion}: {error}")
                conexion.close()


def iniciar_worker_celery():

    import shutil
    import importlib.util

    # 🔍 Verificar si celery está instalado
    if not _esta_celery_instalado():
        return _crear_proceso_simulado("⚠️ Celery no está instalado. Las tareas se ejecutarán de forma síncrona.")

    root_dir = os.path.abspath(os.path.dirname(__file__))
    celery_path = _obtener_ruta_celery()

    if not celery_path:
        return _crear_proceso_simulado("⚠️ No se encontró el ejecutable de Celery. Asegúrate de que esté instalado o define CELERY_PATH en .env")

    try:
        # 🚀 Iniciar el proceso de Celery
        return _iniciar_proceso_celery(celery_path, root_dir)
    except Exception as error:
        mensaje = f"⚠️ Error al iniciar Celery worker: {error}. Las tareas se ejecutarán de forma síncrona."
        return _crear_proceso_simulado(mensaje)

def _esta_celery_instalado():
    import importlib.util
    celery_spec = importlib.util.find_spec("celery")
    return celery_spec is not None

def _crear_proceso_simulado(mensaje):
    print(mensaje)

    class MockProcess:
        def terminate(self):
            pass

    return MockProcess()

def _obtener_ruta_celery():
    import shutil

    # 1. Intentar obtener la ruta de la variable de entorno
    celery_path = os.getenv("CELERY_PATH")
    if celery_path and os.path.exists(celery_path):
        return celery_path

    # 2. Buscar en el entorno virtual actual (.venv)
    # Determinar la ruta según el sistema operativo
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Rutas posibles para diferentes entornos virtuales y sistemas operativos
    posibles_rutas = [
        # .venv (punto al inicio)
        os.path.join(base_dir, ".venv", "bin", "celery"),                # Unix/Mac
        os.path.join(base_dir, ".venv", "Scripts", "celery.exe"),        # Windows
        os.path.join(base_dir, ".venv", "Scripts", "celery"),            # Windows (sin extensión)
        # venv (sin punto)
        os.path.join(base_dir, "venv", "bin", "celery"),                 # Unix/Mac
        os.path.join(base_dir, "venv", "Scripts", "celery.exe"),         # Windows
        os.path.join(base_dir, "venv", "Scripts", "celery"),             # Windows (sin extensión)
    ]

    # Verificar cada ruta posible
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            return ruta

    # 3. Buscar en el PATH del sistema
    system_path = shutil.which("celery")
    if system_path:
        return system_path

    # 4. Último recurso: usar "celery" (podría fallar si no está en el PATH)
    return "celery"

def _iniciar_proceso_celery(celery_path, root_dir):
    # 🔇 Configurar para suprimir la mayoría de los mensajes
    comando = [celery_path, "-A", "tareas.celery", "worker", 
              "--loglevel=critical", "--quiet"]

    # 🚀 Iniciar el proceso con salida redirigida
    process = subprocess.Popen(comando, cwd=root_dir, 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)

    # ✅ Mostrar mensaje de éxito
    print("✅ Worker Celery iniciado correctamente.")

    return process

# La función configurar_argumentos se ha movido a utils/config.py

def _iniciar_modo_servidor(args):
    print(f"🌍 Iniciando Servidor de Archivos Seguro en {args.host}:{args.port}...")
    if args.host != "127.0.0.1" and args.host != "localhost":
        print(f"   ℹ️  Si tienes problemas de conexión, verifica que la dirección IP sea accesible desde tus clientes.")
        print(f"   ℹ️  Para usar la dirección local estándar, ejecuta con: -H 127.0.0.1 o modifica SERVIDOR_HOST en .env")
    worker_process = iniciar_worker_celery()

    try:
        iniciar_servidor_ssl(args.host, args.port, args.directorio)
    except KeyboardInterrupt:
        print("\n🛑 Apagando servidor y worker Celery...")
        worker_process.terminate()

def _iniciar_modo_cliente(args):
    cliente_host = os.getenv("CLIENTE_HOST", "127.0.0.1") if args.host == '0.0.0.0' else args.host

    if args.verbose:
        print(f"🌍 Conectando al Servidor de Archivos Seguro en {cliente_host}:{args.port}...")

    iniciar_cliente(cliente_host, args.port)

if __name__ == "__main__":
    # 📋 Obtener argumentos de línea de comandos
    args = configurar_argumentos(modo_dual=True)

    # 📝 Configurar nivel de logging si es verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 🚀 Iniciar en el modo correspondiente
    if args.modo == 'server':
        _iniciar_modo_servidor(args)
    else:
        _iniciar_modo_cliente(args)



# mac

# python /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/main.py -m server
# python /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/main.py -m cliente

# linux

# python /home/juanma/PycharmProjects/computacionII/final/servidorArchivos/main.py -m server
# python /home/juanma/PycharmProjects/computacionII/final/servidorArchivos/main.py -m cliente