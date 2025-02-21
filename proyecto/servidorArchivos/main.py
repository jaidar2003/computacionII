import sys
import os
import logging
import ssl
import socket
import threading
from servidor import iniciar_servidor, manejar_cliente
from comandos import manejar_comando
from seguridad import autenticar_usuario_en_servidor
from baseDatos.db import insertar_usuario

# Asegurar que 'proyecto/' esté en sys.path para que Python encuentre 'servidorArchivos'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Inicializar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DIRECTORIO_BASE = "archivos_servidor"

# Ruta de los certificados SSL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "..", "certificados", "certificado.pem")
KEY_PATH = os.path.join(BASE_DIR, "..", "certificados", "llave.pem")


def crear_tablas():
    """Crea un usuario admin en la base de datos si no existe."""
    insertar_usuario("admin", "admin123", "lectura,escritura")


def iniciar_servidor_ssl():
    """Inicializa el servidor con SSL."""
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    try:
        contexto.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)
    except FileNotFoundError:
        logging.error("❌ ERROR: No se encontraron los certificados SSL.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind(('127.0.0.1', 5000))
        servidor.listen(5)
        logging.info("✅ Servidor seguro iniciado en 127.0.0.1:5000")

        while True:
            conexion, direccion = servidor.accept()
            conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
            threading.Thread(target=manejar_cliente, args=(conexion_ssl, direccion)).start()


if __name__ == "__main__":
    print("🌍 Iniciando Servidor de Archivos Seguro...\n")
    iniciar_servidor_ssl()  # Servidor seguro con SSL
