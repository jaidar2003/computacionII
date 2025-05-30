"""
🖥️ Cliente de Línea de Comandos para el Servidor de Archivos
----------------------------------------------------------
Este módulo implementa un cliente de línea de comandos para interactuar
con el servidor de archivos seguro.

Características principales:
- 🔒 Conexión segura mediante SSL
- 👤 Autenticación de usuarios
- 📝 Registro de nuevos usuarios
- 💻 Interfaz de línea de comandos para operaciones con archivos
- 🔍 Cálculo de hash para verificación de integridad

El cliente permite realizar operaciones como listar, crear, eliminar y
renombrar archivos en el servidor, así como solicitar cambios de permisos.
"""

import socket
import ssl
import sys
import os
import logging
from dotenv import load_dotenv

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 📦 Cargar variables de entorno
load_dotenv()

# 🔄 Configuración de logging
logger = logging.getLogger(__name__)

# 📚 Importaciones de módulos propios
from server.comandos import manejar_comando
from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario
from cli.utils import input_password, calcular_hash_archivo
from cli.interface import mostrar_banner, mostrar_menu_principal, mostrar_comandos_disponibles
from cli.mensajes import ERROR_CREDENCIALES_INVALIDAS, MENSAJE_DESCONECTAR, MENSAJE_ENVIO_HASH
from cli.estilos import ANSI_VERDE, ANSI_RESET, ANSI_ROJO

# 🔧 Constantes
DIRECTORIO_BASE = os.getenv("CLIENTE_DIR", "servidorArchivos")
BUFFER_SIZE = 1024  # Tamaño del buffer para recibir datos

def iniciar_cliente(host, port):
    """
    🚀 Inicia el cliente y establece conexión con el servidor.

    Args:
        host (str): Dirección IP o nombre del servidor
        port (int): Puerto del servidor
    """
    logger.info(f"🌐 Iniciando cliente para conectar a {host}:{port}")

    try:
        # 🔒 Configurar contexto SSL
        conexion_ssl = _establecer_conexion_ssl(host, port)

        # 👋 Recibir mensajes de bienvenida
        _recibir_mensajes_bienvenida(conexion_ssl)

        # 🔑 Autenticar o registrar usuario
        if not _manejar_autenticacion(conexion_ssl):
            return

        # 💻 Procesar comandos del usuario
        _procesar_comandos(conexion_ssl)

    except Exception as error:
        logger.error(f"❌ Error en el cliente: {error}")
        print(f"❌ Error: {error}")

def _establecer_conexion_ssl(host, port):
    """
    🔒 Establece una conexión SSL con el servidor.

    Args:
        host (str): Dirección IP o nombre del servidor
        port (int): Puerto del servidor

    Returns:
        ssl.SSLSocket: Socket SSL conectado al servidor
    """
    # Configurar contexto SSL sin verificación de certificado
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE

    # Establecer conexión
    sock = socket.create_connection((host, port))
    conexion_ssl = contexto.wrap_socket(sock, server_hostname=host)

    logger.debug(f"🔌 Conexión establecida con {host}:{port}")
    return conexion_ssl

def _recibir_mensajes_bienvenida(conexion):
    """
    👋 Recibe y muestra los mensajes de bienvenida del servidor.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor
    """
    # Recibir y mostrar mensajes de bienvenida
    for _ in range(2):  # El servidor envía dos mensajes
        mensaje = conexion.recv(BUFFER_SIZE).decode('utf-8')
        print(ANSI_VERDE + mensaje + ANSI_RESET)

def _manejar_autenticacion(conexion):
    """
    🔑 Maneja el proceso de autenticación o registro de usuario.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor

    Returns:
        bool: True si la autenticación fue exitosa, False en caso contrario
    """
    while True:
        mostrar_menu_principal()
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            # 🔑 Iniciar sesión
            if _iniciar_sesion(conexion):
                return True
            # Si la autenticación falla, continuamos en el bucle para mostrar el menú de nuevo

        elif opcion == '2':
            # 📝 Registrar nuevo usuario
            _registrar_usuario(conexion)
            # Después de registrar, continuamos en el bucle para que el usuario inicie sesión

        elif opcion == '3':
            # 🚪 Salir
            _enviar_comando(conexion, "SALIR")
            print(MENSAJE_DESCONECTAR)
            return False

        else:
            print(f"❌ Opción no válida: {opcion}")

def _iniciar_sesion(conexion):
    """
    🔑 Inicia sesión con un usuario existente.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor

    Returns:
        bool: True si la autenticación fue exitosa, False en caso contrario
    """
    # Solicitar credenciales
    usuario = input("Usuario: ")
    _enviar_mensaje(conexion, f"{usuario}")
    conexion.recv(BUFFER_SIZE)  # Recibir prompt de contraseña

    password = input_password("Contraseña: ")
    _enviar_mensaje(conexion, f"{password}")

    # Verificar respuesta
    respuesta_auth = conexion.recv(BUFFER_SIZE).decode('utf-8')
    if "✅ Autenticación exitosa" in respuesta_auth:
        print(ANSI_VERDE + respuesta_auth + ANSI_RESET)
        mostrar_comandos_disponibles("lectura")
        return True
    else:
        print(ANSI_ROJO + ERROR_CREDENCIALES_INVALIDAS + ANSI_RESET)
        return False

def _registrar_usuario(conexion):
    """
    📝 Registra un nuevo usuario en el servidor.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor
    """
    nuevo_usuario = input("Nuevo usuario: ")
    nueva_password = input_password("Nueva contraseña: ")

    _enviar_comando(conexion, f"REGISTRAR {nuevo_usuario} {nueva_password}")
    respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')

    if "✅" in respuesta:
        print(ANSI_VERDE + respuesta + ANSI_RESET)
        print(ANSI_VERDE + "👤 Por favor, inicie sesión con sus nuevas credenciales." + ANSI_RESET)
    else:
        print(ANSI_ROJO + respuesta + ANSI_RESET)

def _procesar_comandos(conexion):
    """
    💻 Procesa los comandos del usuario y los envía al servidor.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor
    """
    while True:
        # Recibir prompt del servidor
        prompt = conexion.recv(BUFFER_SIZE).decode('utf-8')

        # Solicitar comando al usuario
        comando = input(prompt)

        # Procesar comando especial CREAR para añadir hash
        if comando.upper().startswith("CREAR "):
            comando = _procesar_comando_crear(comando)

        # Enviar comando al servidor
        _enviar_mensaje(conexion, comando)

        # Salir si el comando es SALIR
        if comando.upper() == "SALIR":
            print(MENSAJE_DESCONECTAR)
            break

        # Mostrar respuesta del servidor
        respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
        print(respuesta)

def _procesar_comando_crear(comando):
    """
    📄 Procesa el comando CREAR para añadir hash del archivo.

    Args:
        comando (str): Comando CREAR original

    Returns:
        str: Comando modificado con hash si corresponde
    """
    partes = comando.split()
    if len(partes) == 2:
        archivo_local = input("Ruta al archivo local: ")
        if os.path.exists(archivo_local):
            hash_archivo = calcular_hash_archivo(archivo_local)
            if hash_archivo:
                comando_modificado = f"{partes[0]} {partes[1]} {hash_archivo}"
                print(MENSAJE_ENVIO_HASH.format(comando=comando_modificado))
                return comando_modificado
    return comando

def _enviar_mensaje(conexion, mensaje):
    """
    📤 Envía un mensaje al servidor.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor
        mensaje (str): Mensaje a enviar
    """
    conexion.sendall(f"{mensaje}\n".encode('utf-8'))

def _enviar_comando(conexion, comando):
    """
    📤 Envía un comando al servidor.

    Args:
        conexion (ssl.SSLSocket): Conexión SSL con el servidor
        comando (str): Comando a enviar
    """
    logger.debug(f"📤 Enviando comando: {comando}")
    _enviar_mensaje(conexion, comando)


if __name__ == "__main__":
    # Configurar logging para escribir a un archivo en lugar de la consola
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "historyLogs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=os.path.join(log_dir, 'cliente.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    mostrar_banner()

    # Usar variables de entorno para host y puerto
    host = os.getenv("SERVIDOR_HOST", "127.0.0.1")
    port = int(os.getenv("SERVIDOR_PORT", 1608))

    # Si el host es 0.0.0.0 (escucha en todas las interfaces), conectar a localhost
    cliente_host = "localhost" if host == "0.0.0.0" else host

    iniciar_cliente(cliente_host, port)
