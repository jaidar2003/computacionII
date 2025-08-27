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
import re
from dotenv import load_dotenv

# 🛡️ Ignorar advertencias de deprecación
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# 📚 Importaciones de módulos propios
from server.servidor import manejar_cliente
from baseDeDatos.db import crear_tablas
from utils.config import verificar_configuracion_env, crear_directorio_si_no_existe, configurar_argumentos
from utils.config import CERT_PATH, KEY_PATH, BASE_DIR
from utils.network import crear_socket_servidor, configurar_contexto_ssl, verificar_stack
from utils.ip import obtener_ip_local

# 📝 Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Verificar configuración del archivo .env
verificar_configuracion_env()

# ⚙️ Crear tablas si no existen
crear_tablas()

def actualizar_ip_en_env(nueva_ip):
    env_path = os.path.join(BASE_DIR, '.env')
    
    # Leer el contenido actual del archivo .env
    with open(env_path, 'r') as file:
        contenido = file.read()
    
    # Reemplazar la IP actual con la nueva IP
    patron = r'SERVER_HOST=.*'
    nuevo_contenido = re.sub(patron, f'SERVER_HOST={nueva_ip}', contenido)
    
    # Escribir el nuevo contenido al archivo .env
    with open(env_path, 'w') as file:
        file.write(nuevo_contenido)

def iniciar_servidor_ssl(host=None, port=None, directorio=None):
    # Usar valores predeterminados si no se proporcionan
    host = host or os.getenv("SERVER_HOST", "0.0.0.0")
    port = port or int(os.getenv("SERVER_PORT", 5005))
    directorio = directorio or os.getenv("SERVIDOR_DIR", os.path.join(os.path.dirname(BASE_DIR), "archivos"))
    # 📂 Asegurar que el directorio de archivos exista
    crear_directorio_si_no_existe(directorio)

    # 🔒 Configurar contexto SSL
    contexto = configurar_contexto_ssl(CERT_PATH, KEY_PATH)
    if not contexto:
        return

    try:
        # 🌐 Verificar stack de red disponible (IPv4/IPv6)
        stack_disponible = verificar_stack()
        
        if not stack_disponible['ipv4'] and not stack_disponible['ipv6']:
            logging.error("❌ No hay stack de red disponible (ni IPv4 ni IPv6)")
            print("❌ No se pudo iniciar el servidor: No hay stack de red disponible")
            return
            
        print("🔍 Verificación de stack de red:")
        if stack_disponible['ipv4']:
            print("   ✅ IPv4 (0.0.0.0) disponible")
        else:
            print("   ❌ IPv4 no disponible")
            
        if stack_disponible['ipv6']:
            print("   ✅ IPv6 (::) disponible")
        else:
            print("   ❌ IPv6 no disponible")
        
        # 🌐 Configurar sockets para IPv4 e IPv6 según disponibilidad
        sockets_servidor = crear_socket_servidor(host, port, stack_disponible=stack_disponible)

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
            # 🧵 Print informativo de hilo de socket levantado
            family_type = "IPv6" if sock.family == socket.AF_INET6 else "IPv4"
            print(f"🧵 Hilo de socket {family_type} levantado")

        # Esperar a que los hilos terminen (o usar algún mecanismo de señalización)
        try:
            for hilo in hilos:
                hilo.join()
        except KeyboardInterrupt:
            print("\n🛑 Apagando servidor...")

    except OSError as error:
        if "No se pudo crear un socket para escuchar conexiones" in str(error):
            # Obtener la IP local correcta
            ip_local = obtener_ip_local()
            print(f"\n❌ ERROR: No se pudo iniciar el servidor en {host}")
            print(f"❌ Si te equivocaste con la dirección IP, el servidor no puede conectarse a {host}")
            print(f"ℹ️ La dirección IP local detectada es: {ip_local}")
            
            # Actualizar automáticamente la IP en el archivo .env
            print(f"🔄 Actualizando automáticamente SERVER_HOST={ip_local} en el archivo .env")
            actualizar_ip_en_env(ip_local)
            print(f"✅ Archivo .env actualizado correctamente. Reinicia el servidor para aplicar los cambios.")
            print(f"ℹ️ Para usar esta IP manualmente, ejecuta el servidor con: -H {ip_local}")
            
            # Salir con código de error
            sys.exit(1)
        else:
            logging.error(f"❌ Error al iniciar el servidor: {error}")
    except Exception as error:
        logging.error(f"❌ Error al iniciar el servidor: {error}")

# Conjunto global para rastrear IPs que ya se han conectado
_ips_conectadas = set()

def _escuchar_conexiones_socket(servidor, contexto, directorio):
    family_type = "IPv6" if servidor.family == socket.AF_INET6 else "IPv4"
    print(f"👂 Esperando conexiones {family_type} entrantes...")
    
    global _ips_conectadas
    
    try:
        while True:
            try:
                # Aceptar conexión (bloqueante)
                conexion, direccion = servidor.accept()
                # Extraer solo la dirección IP (primer elemento de la tupla)
                ip_cliente = direccion[0]
                logging.info(f"✅ Nueva conexión desde {ip_cliente} ({family_type})")
                
                # Solo mostrar mensaje si es la primera vez que vemos esta IP
                if ip_cliente not in _ips_conectadas:
                    print(f"✅ Nueva conexión desde {ip_cliente} ({family_type})")
                    _ips_conectadas.add(ip_cliente)

                try:
                    # Envolver con SSL
                    conexion_ssl = contexto.wrap_socket(conexion, server_side=True)

                    # Iniciar hilo para manejar cliente
                    threading.Thread(
                        target=manejar_cliente,
                        args=(conexion_ssl, direccion, directorio),
                        daemon=True
                    ).start()
                    # 🧵 Print informativo de hilo de cliente levantado
                    print(f"🧵 Hilo para cliente {ip_cliente} ({family_type}) levantado")
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
    return None

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
        return None

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
    
    # Verificar si la IP proporcionada es diferente de la configurada en .env
    ip_env = os.getenv("SERVER_HOST", "127.0.0.1")
    if args.host != ip_env:
        print(f"   ℹ️  La dirección IP proporcionada ({args.host}) es diferente de la configurada en .env ({ip_env})")
        print(f"   🔄 Actualizando automáticamente SERVER_HOST={args.host} en el archivo .env")
        actualizar_ip_en_env(args.host)
        print(f"   ✅ Archivo .env actualizado correctamente.")
    
    if args.host != "127.0.0.1" and args.host != "localhost" and args.host != "0.0.0.0":
        print(f"   ℹ️  Si tienes problemas de conexión, verifica que la dirección IP sea accesible desde tus clientes.")
        print(f"   ℹ️  Para usar la dirección local estándar, ejecuta con: -H 127.0.0.1 o modifica SERVER_HOST en .env")
        print(f"   ℹ️  El sistema intentará detectar automáticamente tu IP local si la configurada no es válida.")
    worker_process = iniciar_worker_celery()

    try:
        iniciar_servidor_ssl(args.host, args.port, args.directorio)
    except KeyboardInterrupt:
        print("\n🛑 Apagando servidor y worker Celery...")
        if worker_process:
            worker_process.terminate()

def _iniciar_modo_api(args):
    print(f"🚀 Iniciando API Flask en 0.0.0.0:5007...")
    print(f"   ℹ️  Asegúrate de que el servidor de archivos esté en ejecución en {args.host}:{args.port}")

    # Actualizar las variables de entorno para la conexión al servidor
    os.environ["SERVER_HOST"] = args.host
    os.environ["SERVER_PORT"] = str(args.port)

    flask_thread = iniciar_servidor_flask()

    try:
        # Mantener el proceso en ejecución
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Apagando API Flask...")

def _iniciar_modo_cli(args):
    print(f"🖥️ Iniciando CLI del Servidor de Archivos...")
    
    # Restaurar los argumentos originales y procesarlos para el CLI
    import sys
    import os
    
    # Obtener los argumentos originales completos
    original_args = sys.argv.copy()
    
    # Encontrar el índice donde aparece 'cli'
    cli_index = -1
    for i, arg in enumerate(original_args):
        if arg == 'cli' or (i > 0 and original_args[i-1] in ['-m', '--modo'] and arg == 'cli'):
            cli_index = i
            break
    
    # Construir nuevos argumentos para el CLI
    if cli_index >= 0 and cli_index + 1 < len(original_args):
        # Tomar todos los argumentos después de 'cli'
        cli_args = original_args[cli_index + 1:]
    else:
        cli_args = []
    
    # Configurar variables de entorno para el servidor si se especificaron
    if args.host:
        os.environ["SERVER_HOST"] = args.host
    if args.port:
        os.environ["SERVER_PORT"] = str(args.port)
    
    # Verificar si se solicitó el modo simple o menu
    use_simple_mode = False
    use_menu_mode = False
    
    for arg in cli_args[:]:  # Usar copia para poder modificar durante iteración
        if arg == '--simple':
            use_simple_mode = True
            cli_args.remove('--simple')
            break
        elif arg == '--menu':
            use_menu_mode = True
            cli_args.remove('--menu')
            break
    
    # Si no se especifica ningún argumento, usar modo menu por defecto
    if not cli_args and not use_simple_mode:
        use_menu_mode = True
    
    # Reconstruir sys.argv para el CLI
    sys.argv = [original_args[0]] + cli_args
    
    # Ejecutar el CLI en el modo correspondiente
    if use_simple_mode:
        from cli.simple.simple_menu import main as simple_main
        simple_main()
    elif use_menu_mode:
        from cli.menu_cli import main as menu_main
        menu_main()
    else:
        from cli.cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    # 📋 Obtener argumentos de línea de comandos
    args = configurar_argumentos(modo_dual=True)

    # 📝 Configurar nivel de logging si es verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 🚀 Iniciar en el modo correspondiente
    if args.modo == 'server':
        _iniciar_modo_servidor(args)
    elif args.modo == 'api':
        _iniciar_modo_api(args)
    elif args.modo == 'cli':
        _iniciar_modo_cli(args)
