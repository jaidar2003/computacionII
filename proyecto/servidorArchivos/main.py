import sys
import os

# Asegurar que 'proyecto/' esté en sys.path para que Python encuentre 'servidorArchivos'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from servidorArchivos.comandos import manejar_comando
from servidorArchivos.seguridad import autenticar_usuario_en_servidor
from servidorArchivos.baseDatos.db import insertar_usuario  # ✅ Agregada esta importación

# Inicializar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DIRECTORIO_BASE = "archivos_servidor"  # ✅ Agregar variable global

def crear_tablas():
    """Crea un usuario admin en la base de datos."""
    insertar_usuario("admin", "admin123", "lectura,escritura")

def manejar_cliente(conexion_ssl, direccion):
    try:
        logging.info(f"Conexión aceptada desde {direccion}")
        conexion_ssl.sendall("Bienvenido al servidor. Autenticación requerida.\nUsuario: ".encode('utf-8'))
        usuario = conexion_ssl.recv(1024).decode().strip()
        conexion_ssl.sendall("Contraseña: ".encode('utf-8'))
        password = conexion_ssl.recv(1024).decode().strip()

        if not autenticar_usuario_en_servidor(usuario, password):  # ✅ Se cambió autenticar_usuario por autenticar_usuario_en_servidor
            conexion_ssl.sendall("Credenciales inválidas. Desconectando.\n".encode('utf-8'))
            conexion_ssl.close()
            return

        conexion_ssl.sendall("Autenticación exitosa!\n".encode('utf-8'))

        while True:
            conexion_ssl.sendall(b"> ")
            comando = conexion_ssl.recv(1024).decode().strip()
            if comando.upper() == "SALIR":
                conexion_ssl.sendall(b"Desconectando...\n")
                break
            respuesta = manejar_comando(comando, DIRECTORIO_BASE)  # ✅ Ahora usa la variable global correcta
            conexion_ssl.sendall(respuesta.encode())
    except Exception as e:
        logging.error(f"Error con cliente {direccion}: {e}")
    finally:
        conexion_ssl.close()
        logging.info(f"Conexión cerrada con {direccion}")
