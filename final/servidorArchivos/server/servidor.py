import socket
import ssl
import threading
import logging
import os
import sys
import argparse
from dotenv import load_dotenv

# Configuración básica de sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importaciones con fallback
try:
    from server.comandos import manejar_comando
    from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from comandos import manejar_comando
    from seguridad import autenticar_usuario_en_servidor, registrar_usuario

from baseDeDatos.db import log_evento
from utils.config import CERT_PATH, KEY_PATH
from utils.config import crear_directorio_si_no_existe, configurar_argumentos
from utils.network import crear_socket_servidor, configurar_contexto_ssl

load_dotenv()

# Configuración de logging a archivo en final/historial
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Directorio "final"
log_dir = os.path.join(base_dir, "historial")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, 'servidor.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Conjunto global para rastrear IPs desconectadas (solo para mostrar una vez)
_ips_desconectadas = set()

def _enviar_mensaje(conexion, mensaje: str):
    conexion.sendall(mensaje.encode('utf-8'))

def _recibir_mensaje(conexion, prompt: str | None = None) -> str:
    if prompt:
        _enviar_mensaje(conexion, prompt)
    return conexion.recv(1024).decode().strip()

def _manejar_registro(conexion, comando_registro: str):
    partes = comando_registro.split()
    if len(partes) != 3:
        _enviar_mensaje(conexion, "❌ Formato incorrecto. Usa: REGISTRAR usuario contraseña\n")
        return

    _, nuevo_usuario, nueva_contraseña = partes
    respuesta = registrar_usuario(nuevo_usuario, nueva_contraseña)
    _enviar_mensaje(conexion, f"{respuesta}\n")

    if respuesta.startswith("✅"):
        _enviar_mensaje(conexion, "👤 Ahora inicia sesión con tu nuevo usuario.\n")

def _autenticar_usuario(conexion):
    while True:
        usuario = _recibir_mensaje(conexion, "👤 Usuario: ")

        # Registro inline
        if usuario.upper().startswith("REGISTRAR"):
            _manejar_registro(conexion, usuario)
            continue

        password = _recibir_mensaje(conexion, "🔒 Contraseña: ")

        datos_usuario = autenticar_usuario_en_servidor(usuario, password)
        if not datos_usuario:
            _enviar_mensaje(conexion, "❌ Credenciales inválidas. Intenta nuevamente.\n")
            continue

        usuario_id, permisos = datos_usuario
        _enviar_mensaje(conexion, f"✅ Autenticación exitosa! Permisos: {permisos}\n")
        return usuario_id, permisos

def _procesar_comandos(conexion, directorio: str, usuario_id: int) -> bool:
    """
    Retorna True si el cliente envió SALIR explícitamente.
    """
    while True:
        comando = _recibir_mensaje(conexion, "\n💻 Ingresar comando ('SALIR' para desconectar): ")

        if comando.upper() == "SALIR":
            _enviar_mensaje(conexion, "🔌 Desconectando...\n")
            return True

        partes = comando.strip().split()
        if partes and partes[0].upper() in ["DESCARGAR", "SUBIR"]:
            # Estos comandos usan la conexión para transferir datos
            respuesta = manejar_comando(comando, directorio, usuario_id, conexion)
        else:
            respuesta = manejar_comando(comando, directorio, usuario_id)

        _enviar_mensaje(conexion, f"📄 {respuesta}\n")

def manejar_cliente(conexion_ssl, direccion, directorio):
    ip_cliente = direccion[0]
    global _ips_desconectadas

    cliente_desconectado = False
    try:
        _enviar_mensaje(conexion_ssl, "🌍 Bienvenido al servidor de archivos seguro.\n")
        usuario_id, permisos = _autenticar_usuario(conexion_ssl)
        cliente_desconectado = _procesar_comandos(conexion_ssl, directorio, usuario_id)

    except Exception as error:
        logging.error(f"❌ Error con cliente {ip_cliente}: {error}")
    finally:
        try:
            conexion_ssl.close()
        except Exception:
            pass

        # Evitar spam si la desconexión viene de la API/loopback
        servidor_ip = socket.gethostbyname(socket.gethostname())
        es_conexion_api = ip_cliente in ("127.0.0.1", "::1", servidor_ip)

        if cliente_desconectado and not es_conexion_api:
            logging.info(f"🔌 Cliente {ip_cliente} desconectado")
            if ip_cliente not in _ips_desconectadas:
                print(f"🔌 Cliente {ip_cliente} desconectado")
                _ips_desconectadas.add(ip_cliente)

def _escuchar_conexiones_socket(servidor_sock: socket.socket, contexto_ssl: ssl.SSLContext, directorio: str):
    family_type = "IPv6" if servidor_sock.family == socket.AF_INET6 else "IPv4"
    try:
        addr = servidor_sock.getsockname()
        if servidor_sock.family == socket.AF_INET6:
            bind_str = f"[{addr[0]}]:{addr[1]}"
        else:
            bind_str = f"{addr[0]}:{addr[1]}"
    except Exception:
        bind_str = "<desconocido>"

    print(f"👂 Esperando conexiones {family_type} en {bind_str} ...")
    logging.info(f"accept() activo para {family_type} en {bind_str}")

    while True:
        try:
            conexion, direccion = servidor_sock.accept()  # bloqueante
            ip_cliente = direccion[0]
            logging.info(f"✅ Nueva conexión desde {ip_cliente} ({family_type})")

            try:
                conexion_ssl = contexto_ssl.wrap_socket(conexion, server_side=True)
            except ssl.SSLError as error:
                logging.error(f"🔒 Error SSL con {ip_cliente}: {error}")
                try:
                    conexion.close()
                except Exception:
                    pass
                continue

            threading.Thread(
                target=manejar_cliente,
                args=(conexion_ssl, direccion, directorio),
                daemon=True
            ).start()

        except Exception as e:
            logging.error(f"❌ Error al aceptar conexión {family_type}: {e}")

def iniciar_servidor(host=None, port=None, directorio=None):
    # Defaults
    host = host or os.getenv("SERVER_HOST", "0.0.0.0")      # ignorado en hardening por utils.network
    port = port or int(os.getenv("SERVER_PORT", 5005))
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    directorio = directorio or os.getenv("SERVIDOR_DIR", os.path.join(os.path.dirname(base_dir), "archivos"))

    # Asegurar directorio de archivos
    crear_directorio_si_no_existe(directorio)

    # Contexto SSL
    contexto = configurar_contexto_ssl(CERT_PATH, KEY_PATH)
    if not contexto:
        return

    try:
        # ⚙️ Crear sockets (IPv4 + IPv6, V6ONLY=1) — Variante 2
        sockets_servidor = crear_socket_servidor(host, port)

        if not sockets_servidor:
            logging.error("❌ No se pudieron crear sockets para escuchar conexiones")
            return

        print(f"🌍 Servidor de Archivos Seguro escuchando en {len(sockets_servidor)} interfaces:")
        for i, sock in enumerate(sockets_servidor, 1):
            fam = "IPv6" if sock.family == socket.AF_INET6 else "IPv4"
            try:
                addr = sock.getsockname()
                bind_str = f"[{addr[0]}]:{addr[1]}" if sock.family == socket.AF_INET6 else f"{addr[0]}:{addr[1]}"
            except Exception:
                bind_str = "<desconocido>"
            print(f"   ✅ Socket {i}: {fam} en {bind_str}")

        # 🧵 Lanzar un hilo accept() por socket
        hilos = []
        for sock in sockets_servidor:
            hilo = threading.Thread(
                target=_escuchar_conexiones_socket,
                args=(sock, contexto, directorio),
                daemon=True
            )
            hilos.append(hilo)
            hilo.start()

        # Mantener proceso vivo hasta Ctrl+C
        try:
            for hilo in hilos:
                hilo.join()
        except KeyboardInterrupt:
            logging.info("👋 Servidor detenido por el usuario")
            print("\n👋 Servidor detenido. ¡Hasta pronto!")

    except Exception as error:
        logging.error(f"❌ Error en el servidor: {error}")

if __name__ == "__main__":
    print("✅ Módulo servidor.py cargado correctamente.")
    print("✅ Importación de comandos, seguridad y baseDeDatos.db exitosa.")

    # Activamos el modo dual/hardening en el parser de argumentos
    args = configurar_argumentos(modo_dual=True)

    # Verbose opcional
    if getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)

    # 🚀 Iniciar servidor
    iniciar_servidor(args.host, args.port, args.directorio)
