import socket
import ssl
import threading
import logging
import os
from comandos import manejar_comando
from seguridad import autenticar_usuario_en_servidor, registrar_usuario

HOST = '127.0.0.1'
PORT = 5000
DIRECTORIO_BASE = "archivos_servidor"


def manejar_cliente(conexion_ssl, direccion):
    try:
        logging.info(f"Conexión aceptada desde {direccion}")
        conexion_ssl.sendall(
            "Bienvenido al servidor. Escribe 'REGISTRAR usuario contraseña' para registrarte o ingresa tus credenciales.\n".encode(
                'utf-8'))

        while True:
            conexion_ssl.sendall("Usuario: ".encode('utf-8'))
            usuario = conexion_ssl.recv(1024).decode().strip()

            if usuario.upper().startswith("REGISTRAR"):
                _, nuevo_usuario, nueva_contraseña = usuario.split()
                respuesta = registrar_usuario(nuevo_usuario, nueva_contraseña)
                conexion_ssl.sendall(respuesta.encode('utf-8'))
                continue  # Volver al inicio para que inicie sesión

            conexion_ssl.sendall("Contraseña: ".encode('utf-8'))
            password = conexion_ssl.recv(1024).decode().strip()

            datos_usuario = autenticar_usuario_en_servidor(usuario, password)
            if not datos_usuario:
                conexion_ssl.sendall("Credenciales inválidas. Intenta nuevamente.\n".encode('utf-8'))
                continue

            usuario_id, permisos = datos_usuario
            conexion_ssl.sendall(f"Autenticación exitosa! Permisos: {permisos}\n".encode('utf-8'))
            break  # Salir del bucle de autenticación y continuar

        # Bucle para procesar comandos del usuario autenticado
        while True:
            conexion_ssl.sendall(b"> ")
            comando = conexion_ssl.recv(1024).decode().strip()
            if comando.upper() == "SALIR":
                conexion_ssl.sendall(b"Desconectando...\n")
                break
            respuesta = manejar_comando(comando, DIRECTORIO_BASE, usuario_id)
            conexion_ssl.sendall(respuesta.encode())
    except Exception as e:
        logging.error(f"Error con cliente {direccion}: {e}")
    finally:
        conexion_ssl.close()


def iniciar_servidor():
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # Obtener la ruta absoluta del directorio del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    # Construir las rutas de los certificados de manera dinámica
    cert_path = os.path.join(BASE_DIR, "certificados", "certificado.pem")
    key_path = os.path.join(BASE_DIR, "certificados", "llave.pem")

    try:
        contexto.load_cert_chain(certfile=cert_path, keyfile=key_path)
    except FileNotFoundError:
        logging.error(f"Error: No se encontraron los certificados en {cert_path} o {key_path}.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((HOST, PORT))
        servidor.listen(5)
        logging.info(f"Servidor escuchando en {HOST}:{PORT}")

        while True:
            conexion, direccion = servidor.accept()
            try:
                conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
                threading.Thread(target=manejar_cliente, args=(conexion_ssl, direccion)).start()
            except ssl.SSLError as e:
                logging.error(f"Error SSL con {direccion}: {e}")
                conexion.close()


if __name__ == "__main__":
    iniciar_servidor()
