# 🚀 Servidor de Archivos Seguro
# ----------------------------
# Este módulo es el punto de entrada principal para la aplicación.
# Permite iniciar tanto el servidor como el cliente.

import sys
import os
import argparse
import logging
import socket
import ssl
import threading
import warnings
import subprocess
from dotenv import load_dotenv

# 🛡️ Ignorar advertencias de deprecación
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 📚 Importaciones de módulos propios
from server.servidor import manejar_cliente
from base_datos.db import crear_tablas
from cli.cliente import iniciar_cliente

# 📦 Cargar variables de entorno
load_dotenv()

# 📝 Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔐 Rutas absolutas a certificados SSL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "certificados", "certificado.pem")
KEY_PATH = os.path.join(BASE_DIR, "certificados", "llave.pem")

# 🌐 Configuración del servidor desde variables de entorno
SERVIDOR_HOST = os.getenv("SERVIDOR_HOST", "127.0.0.1")
SERVIDOR_PORT = int(os.getenv("SERVIDOR_PORT", 1608))
SERVIDOR_DIR = os.getenv("SERVIDOR_DIR", "archivos_servidor")

# ⚙️ Crear tablas si no existen
crear_tablas()

def iniciar_servidor_ssl(host=SERVIDOR_HOST, port=SERVIDOR_PORT, directorio=SERVIDOR_DIR):
    # 🌐 Inicia el servidor SSL que maneja conexiones seguras de clientes
    # 📂 Asegurar que el directorio de archivos exista
    _crear_directorio_si_no_existe(directorio)

    # 🔒 Configurar contexto SSL
    contexto = _configurar_contexto_ssl()
    if not contexto:
        return

    try:
        # 🌐 Configurar socket
        socket_servidor = _crear_socket_servidor(host, port)

        # 👂 Escuchar conexiones
        _escuchar_conexiones(socket_servidor, contexto, directorio)
    except Exception as error:
        logging.error(f"❌ Error al iniciar el servidor: {error}")

def _crear_directorio_si_no_existe(directorio):
    # Crea el directorio de archivos si no existe.
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        logging.info(f"📁 Directorio creado: {directorio}")

def _configurar_contexto_ssl():
    # Configura y retorna el contexto SSL para el servidor.
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        logging.error("❌ ERROR: No se encontraron los certificados SSL.")
        return None

    contexto.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)
    return contexto

def _crear_socket_servidor(host, port):
    # Crea y configura el socket del servidor.
    addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    family, socktype, proto, canonname, sockaddr = addr_info[0]

    servidor = socket.socket(family, socktype, proto)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, port))
    servidor.listen(5)
    logging.info(f"✅ Servidor seguro iniciado en {host}:{port}")

    return servidor

def _escuchar_conexiones(servidor, contexto, directorio):
    # Escucha y maneja las conexiones entrantes.
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
    # 🔄 Inicia worker Celery o retorna un objeto simulado si no está disponible

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
    # Verifica si el módulo Celery está instalado.
    import importlib.util
    celery_spec = importlib.util.find_spec("celery")
    return celery_spec is not None

def _crear_proceso_simulado(mensaje):
    # Crea un objeto que simula un proceso con método terminate().
    print(mensaje)

    class MockProcess:
        def terminate(self):
            pass

    return MockProcess()

def _obtener_ruta_celery():
    # Obtiene la ruta al ejecutable de Celery.
    import shutil
    return os.getenv("CELERY_PATH", shutil.which("celery")) or "celery"

def _iniciar_proceso_celery(celery_path, root_dir):
    # Inicia el proceso de Celery worker.
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

def _configurar_argumentos():
    # 📋 Configura y parsea los argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='🔐 Cliente/Servidor de Archivos Seguro',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-m', '--modo', 
        type=str, 
        choices=['cliente', 'server'], 
        default='server',
        help='Modo de ejecución: cliente o server'
    )

    parser.add_argument(
        '-H', '--host', 
        type=str, 
        default=SERVIDOR_HOST,
        help=f'Dirección IP del servidor'
    )

    parser.add_argument(
        '-p', '--port', 
        type=int, 
        default=SERVIDOR_PORT,
        help=f'Puerto del servidor'
    )

    parser.add_argument(
        '-d', '--directorio', 
        type=str, 
        default=SERVIDOR_DIR,
        help=f'Directorio base para archivos'
    )

    parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Mostrar logs detallados'
    )

    return parser.parse_args()

def _iniciar_modo_servidor(args):
    # 🖥️ Inicia la aplicación en modo servidor
    print(f"🌍 Iniciando Servidor de Archivos Seguro en {args.host}:{args.port}...")
    worker_process = iniciar_worker_celery()

    try:
        iniciar_servidor_ssl(args.host, args.port, args.directorio)
    except KeyboardInterrupt:
        print("\n🛑 Apagando servidor y worker Celery...")
        worker_process.terminate()

def _iniciar_modo_cliente(args):
    # 👤 Inicia la aplicación en modo cliente
    # Si el host es 0.0.0.0 (escucha en todas las interfaces), 
    # conectar a localhost o al host especificado en .env
    cliente_host = os.getenv("CLIENTE_HOST", "127.0.0.1") if args.host == '0.0.0.0' else args.host

    if args.verbose:
        print(f"🌍 Conectando al Servidor de Archivos Seguro en {cliente_host}:{args.port}...")

    iniciar_cliente(cliente_host, args.port)

if __name__ == "__main__":
    # 📋 Obtener argumentos de línea de comandos
    args = _configurar_argumentos()

    # 📝 Configurar nivel de logging si es verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 🚀 Iniciar en el modo correspondiente
    if args.modo == 'server':
        _iniciar_modo_servidor(args)
    else:
        _iniciar_modo_cliente(args)
