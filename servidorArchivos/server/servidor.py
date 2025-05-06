import socket
import ssl
import threading
import logging
import os
from dotenv import load_dotenv
from comandos import *
from seguridad import autenticar_usuario_en_servidor, registrar_usuario
from base_datos.db import log_evento

load_dotenv()

HOST = os.getenv("SERVIDOR_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVIDOR_PORT", 5050))
DIRECTORIO_BASE = os.getenv("SERVIDOR_DIR", "archivos_servidor")

logging.basicConfig(
    filename='servidor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def manejar_cliente(conexion_ssl, direccion, directorio=DIRECTORIO_BASE):
    try:
        logging.info(f"🔗 Conexión aceptada desde {direccion}")
        conexion_ssl.sendall("🌍 Bienvenido al server de archivos seguro.\n".encode('utf-8'))

        while True:
            conexion_ssl.sendall("👤 Usuario: ".encode('utf-8'))
            usuario = conexion_ssl.recv(1024).decode().strip()
            logging.info(f"📥 Usuario recibido: {usuario}")

            if usuario.upper().startswith("REGISTRAR"):
                partes = usuario.split()
                if len(partes) != 3:
                    conexion_ssl.sendall("❌ Formato incorrecto. Usa: REGISTRAR usuario contraseña\n".encode('utf-8'))
                else:
                    _, nuevo_usuario, nueva_contraseña = partes
                    respuesta = registrar_usuario(nuevo_usuario, nueva_contraseña)
                    conexion_ssl.sendall(f"{respuesta}\n".encode('utf-8'))

                    if respuesta.startswith("✅"):
                        conexion_ssl.sendall("👤 Ahora inicia sesión con tu nuevo usuario.\n".encode('utf-8'))
                continue

            conexion_ssl.sendall("🔒 Contraseña: ".encode('utf-8'))
            password = conexion_ssl.recv(1024).decode().strip()
            logging.info(f"🔑 Intentando autenticar usuario {usuario}")

            datos_usuario = autenticar_usuario_en_servidor(usuario, password)
            if not datos_usuario:
                conexion_ssl.sendall("❌ Credenciales inválidas. Intenta nuevamente.\n".encode('utf-8'))
                log_evento(usuario, direccion[0], "AUTENTICACION", "Fallo en la autenticación")
                continue

            usuario_id, permisos = datos_usuario
            conexion_ssl.sendall(f"✅ Autenticación exitosa! Permisos: {permisos}\n".encode('utf-8'))
            logging.info(f"✅ Usuario {usuario} autenticado con permisos: {permisos}")
            log_evento(usuario, direccion[0], "AUTENTICACION", "Inicio de sesión exitoso")
            break

        while True:
            conexion_ssl.sendall("\n💻 Ingresar comando ('SALIR' para desconectar): ".encode('utf-8'))
            comando = conexion_ssl.recv(1024).decode().strip()
            logging.info(f"📥 Comando recibido: {comando}")

            if comando.upper() == "SALIR":
                conexion_ssl.sendall("🔌 Desconectando...\n".encode('utf-8'))
                log_evento(usuario, direccion[0], "SESION", "Desconexión del cliente")
                break

            respuesta = manejar_comando(comando, directorio, usuario_id)
            conexion_ssl.sendall(f"📄 {respuesta}\n".encode('utf-8'))
            log_evento(usuario, direccion[0], "COMANDO", f"Ejecutó: {comando}")

    except Exception as e:
        logging.error(f"❌ Error con cliente {direccion}: {e}")
        log_evento("sistema", direccion[0], "ERROR", str(e))
    finally:
        conexion_ssl.close()
        logging.info(f"🔌 Conexión cerrada con {direccion}")

def iniciar_servidor(host=HOST, port=PORT, directorio=DIRECTORIO_BASE):
    if not os.path.exists(directorio):
        os.makedirs(directorio)

    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    cert_path = os.path.join(BASE_DIR, "certificados", "certificado.pem")
    key_path = os.path.join(BASE_DIR, "certificados", "llave.pem")

    try:
        contexto.load_cert_chain(certfile=cert_path, keyfile=key_path)
    except FileNotFoundError:
        logging.error(f"❌ Error: No se encontraron los certificados en {cert_path} o {key_path}.")
        return

    try:
        addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        family, socktype, proto, canonname, sockaddr = addr_info[0]

        with socket.socket(family, socktype, proto) as servidor:
            servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            servidor.bind((host, port))
            servidor.listen(5)
            logging.info(f"✅ Servidor escuchando en {host}:{port}")

            while True:
                conexion, direccion = servidor.accept()
                try:
                    conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
                    threading.Thread(target=manejar_cliente, args=(conexion_ssl, direccion, directorio)).start()
                except ssl.SSLError as e:
                    logging.error(f"❌ Error SSL con {direccion}: {e}")
                    conexion.close()
    except Exception as e:
        logging.error(f"❌ Error al iniciar el server: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Servidor de Archivos Seguro')
    parser.add_argument('-H', '--host', type=str, default=HOST)
    parser.add_argument('-p', '--port', type=int, default=PORT)
    parser.add_argument('-d', '--directorio', type=str, default=DIRECTORIO_BASE)
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print(f"🌍 Iniciando Servidor de Archivos Seguro en {args.host}:{args.port}...\n")
    iniciar_servidor(args.host, args.port, args.directorio)
