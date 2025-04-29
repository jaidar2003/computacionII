import sys
import os
import argparse

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import socket
import ssl
import threading
from servidor import manejar_cliente
from base_datos.db import crear_tablas
from cliente import iniciar_cliente

# 🎯 Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔐 Rutas absolutas a certificados SSL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "..", "certificados", "certificado.pem")
KEY_PATH = os.path.join(BASE_DIR, "..", "certificados", "llave.pem")

# ⚙️ Crear tablas si no existen
crear_tablas()

def iniciar_servidor_ssl(host='0.0.0.0', port=5050, directorio='archivos_servidor'):
    """
    Inicializa el servidor con SSL.

    Args:
        host (str): Dirección IP del servidor. Por defecto '0.0.0.0' para aceptar conexiones de cualquier interfaz.
        port (int): Puerto en el que escuchará el servidor.
        directorio (str): Directorio base para almacenar los archivos.
    """
    # Crear directorio si no existe
    if not os.path.exists(directorio):
        os.makedirs(directorio)

    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        logging.error("❌ ERROR: No se encontraron los certificados SSL.")
        return

    contexto.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

    # Determinar la familia de direcciones (IPv4 o IPv6)
    try:
        # Intentar resolver la dirección para determinar si es IPv4 o IPv6
        addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        family, socktype, proto, canonname, sockaddr = addr_info[0]

        with socket.socket(family, socktype, proto) as servidor:
            # Permitir reutilizar la dirección
            servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            servidor.bind((host, port))
            servidor.listen(5)
            logging.info(f"✅ Servidor seguro iniciado en {host}:{port}")

            while True:
                conexion, direccion = servidor.accept()
                try:
                    conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
                    threading.Thread(target=manejar_cliente, args=(conexion_ssl, direccion, directorio)).start()
                except ssl.SSLError as e:
                    logging.error(f"❌ Error SSL con {direccion}: {e}")
                    conexion.close()
    except Exception as e:
        logging.error(f"❌ Error al iniciar el servidor: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cliente/Servidor de Archivos Seguro')
    parser.add_argument('-m', '--modo', type=str, choices=['cliente', 'servidor'], default='servidor',
                        help='Modo de ejecución: cliente o servidor (por defecto: servidor)')
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0',
                        help='Dirección IP del servidor (por defecto: 0.0.0.0 para servidor, 127.0.0.1 para cliente)')
    parser.add_argument('-p', '--port', type=int, default=5050,
                        help='Puerto del servidor (por defecto: 5050)')
    parser.add_argument('-d', '--directorio', type=str, default='archivos_servidor',
                        help='Directorio base para archivos (por defecto: archivos_servidor)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mostrar logs detallados')

    args = parser.parse_args()

    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.modo == 'servidor':
        print(f"🌍 Iniciando Servidor de Archivos Seguro en {args.host}:{args.port}...\n")
        iniciar_servidor_ssl(args.host, args.port, args.directorio)
    else:  # modo cliente
        cliente_host = '127.0.0.1' if args.host == '0.0.0.0' else args.host
        if args.verbose:
            print(f"🌍 Conectando al Servidor de Archivos Seguro en {cliente_host}:{args.port}...\n")
        iniciar_cliente(cliente_host, args.port)
