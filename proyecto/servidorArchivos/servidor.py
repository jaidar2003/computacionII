import os
import socket
import ssl
import threading
import logging
from comandos import manejar_comando
from seguridad import autenticar_usuario

HOST = '127.0.0.1'
PORT = 5000
DIRECTORIO_BASE = "archivos_servidor"

def manejar_cliente(conexion_ssl, direccion):
    try:
        logging.info(f"Conexión aceptada desde {direccion}")
        conexion_ssl.sendall("Bienvenido al servidor. Autenticación requerida.\nUsuario: ".encode('utf-8'))
        usuario = conexion_ssl.recv(1024).decode().strip()
        conexion_ssl.sendall("Contraseña: ".encode('utf-8'))
        password = conexion_ssl.recv(1024).decode().strip()

        if not autenticar_usuario(usuario, password):
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
            respuesta = manejar_comando(comando, DIRECTORIO_BASE)
            conexion_ssl.sendall(respuesta.encode())
    except Exception as e:
        logging.error(f"Error con cliente {direccion}: {e}")
    finally:
        conexion_ssl.close()
        logging.info(f"Conexión cerrada con {direccion}")

def iniciar_servidor():
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    contexto.load_cert_chain(certfile="certificados/certificado.pem", keyfile="certificados/llave.pem")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((HOST, PORT))
        servidor.listen(5)
        logging.info(f"Servidor escuchando en {HOST}:{PORT}")

        while True:
            conexion, direccion = servidor.accept()
            conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
            threading.Thread(target=manejar_cliente, args=(conexion_ssl, direccion)).start()

if __name__ == "__main__":
    iniciar_servidor()
