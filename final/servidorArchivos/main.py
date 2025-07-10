import sys
import os
import argparse
import logging
import threading
import warnings
import subprocess
import ssl
import socket
import selectors
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
from utils.config import CERT_PATH, KEY_PATH, BASE_DIR
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
    directorio = directorio or os.getenv("SERVIDOR_DIR", os.path.join(os.path.dirname(BASE_DIR), "archivos"))
    # 📂 Asegurar que el directorio de archivos exista
    crear_directorio_si_no_existe(directorio)

    # 🔒 Configurar contexto SSL
    contexto = configurar_contexto_ssl(CERT_PATH, KEY_PATH)
    if not contexto:
        return

    try:
        # 🌐 Configurar sockets para IPv4 e IPv6
        sockets_servidor = crear_socket_servidor(host, port)

        # Verificar si se crearon sockets
        if not sockets_servidor:
            logging.error("❌ No se pudieron crear sockets para escuchar conexiones")
            return

        # Mostrar información sobre los sockets creados
        print(f"🌍 Servidor escuchando en {len(sockets_servidor)} interfaces:")
        for i, sock in enumerate(sockets_servidor):
            family = "IPv6" if sock.family == socket.AF_INET6 else "IPv4"
            print(f"   ✅ Socket {i+1}: {family}")

        # Crear hilos para cada socket
        hilos = []
        for sock in sockets_servidor:
            hilo = threading.Thread(
                target=_escuchar_conexiones_socket,
                args=(sock, contexto, directorio),
                daemon=True
            )
            hilos.append(hilo)
            hilo.start()

        # Esperar a que los hilos terminen (o usar algún mecanismo de señalización)
        try:
            for hilo in hilos:
                hilo.join()
        except KeyboardInterrupt:
            print("\n🛑 Apagando servidor...")

    except Exception as error:
        logging.error(f"❌ Error al iniciar el servidor: {error}")

def _escuchar_conexiones_socket(servidor, contexto, directorio):
    family_type = "IPv6" if servidor.family == socket.AF_INET6 else "IPv4"
    print(f"👂 Esperando conexiones {family_type} entrantes...")

    try:
        while True:
            try:
                # Aceptar conexión (bloqueante)
                conexion, direccion = servidor.accept()
                # Extraer solo la dirección IP (primer elemento de la tupla)
                ip_cliente = direccion[0]
                logging.info(f"✅ Nueva conexión desde {ip_cliente} ({family_type})")
                print(f"✅ Nueva conexión desde {ip_cliente} ({family_type})")

                try:
                    # Envolver con SSL
                    conexion_ssl = contexto.wrap_socket(conexion, server_side=True)

                    # Iniciar hilo para manejar cliente
                    threading.Thread(
                        target=manejar_cliente,
                        args=(conexion_ssl, direccion, directorio),
                        daemon=True
                    ).start()
                except ssl.SSLError as error:
                    logging.error(f"🔒 Error SSL con {ip_cliente}: {error}")
                    conexion.close()
            except Exception as e:
                logging.error(f"❌ Error al aceptar conexión {family_type}: {e}")
    finally:
        servidor.close()


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

def iniciar_servidor_flask():
    from api.app import app
    import threading
    import logging
    import socket

    # Configurar Flask para que no muestre mensajes de inicio
    # Esto suprime los mensajes "* Running on..." y "* Debug mode: off"
    import flask.cli
    flask.cli.show_server_banner = lambda *args, **kwargs: None

    # Suprimir mensajes de logging de Flask y Werkzeug
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Verificar si el puerto ya está en uso
    flask_port = 5007
    flask_host = '0.0.0.0'

    # Verificar si el puerto ya está en uso
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((flask_host, flask_port))
    sock.close()

    if result == 0:  # Puerto ya está en uso
        print("⚠️  Puerto 5007 ya está en uso. La API REST podría no estar disponible.")
        print("   ℹ️  Intenta detener otros servidores Flask o usa un puerto diferente.")

        # Devolver un hilo simulado para mantener la interfaz consistente
        class MockThread:
            def join(self):
                pass
        return MockThread()

    # Función para ejecutar Flask en un hilo
    def run_flask():
        try:
            # Ejecutar Flask sin mensajes de inicio
            app.run(host=flask_host, port=flask_port, debug=False)
        except Exception as e:
            print(f"❌ Error en el servidor Flask: {e}")

    # Iniciar Flask en un hilo separado
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Mostrar mensajes personalizados con emojis
    print(f"🚀 Servidor Flask API iniciado en {flask_host}:{flask_port}")
    print(f"   ✅ API REST disponible en http://{flask_host}:{flask_port}/api")

    return flask_thread

def _iniciar_modo_servidor(args):
    print(f"🌍 Iniciando Servidor de Archivos Seguro en {args.host}:{args.port}...")
    if args.host != "127.0.0.1" and args.host != "localhost":
        print(f"   ℹ️  Si tienes problemas de conexión, verifica que la dirección IP sea accesible desde tus clientes.")
        print(f"   ℹ️  Para usar la dirección local estándar, ejecuta con: -H 127.0.0.1 o modifica SERVIDOR_HOST en .env")
    worker_process = iniciar_worker_celery()
    flask_thread = iniciar_servidor_flask()  # Iniciar Flask

    try:
        iniciar_servidor_ssl(args.host, args.port, args.directorio)
    except KeyboardInterrupt:
        print("\n🛑 Apagando servidor, worker Celery y API Flask...")
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
