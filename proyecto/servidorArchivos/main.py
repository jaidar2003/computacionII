import sys
import os
import logging
import socket
import ssl
import threading
from servidor import manejar_cliente, iniciar_servidor
from comandos import manejar_comando
from seguridad import autenticar_usuario_en_servidor
from base_datos.db import registrar_usuario, crear_tablas

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


# Agregar 'proyecto/' al sys.path para que Python encuentre 'servidorArchivos'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Inicializar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DIRECTORIO_BASE = "archivos_servidor"

# Ruta de los certificados SSL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "certificados", "certificado.pem")
KEY_PATH = os.path.join(BASE_DIR, "certificados", "llave.pem")

# Crear tablas al iniciar
crear_tablas()

def iniciar_servidor_ssl():
    """Inicializa el servidor con SSL."""
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        logging.error("❌ ERROR: No se encontraron los certificados SSL.")
        return

    contexto.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

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
    iniciar_servidor_ssl()
