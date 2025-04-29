import socket
import ssl
import threading
import logging
import os
from proyecto.servidorArchivos.servidor.comandos import manejar_comando
from proyecto.servidorArchivos.servidor.seguridad import autenticar_usuario_en_servidor, registrar_usuario

HOST = '127.0.0.1'
PORT = 5000
DIRECTORIO_BASE = "archivos_servidor"


def manejar_cliente(conexion_ssl, direccion):
    try:
        logging.info(f"🔗 Conexión aceptada desde {direccion}")
        conexion_ssl.sendall("🌍 Bienvenido al servidor de archivos seguro.\n".encode('utf-8'))

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

                # 🔹 En lugar de `continue`, pedimos de nuevo usuario y contraseña
                conexion_ssl.sendall("👤 Ahora inicia sesión con tu nuevo usuario.\n".encode('utf-8'))
                return  # 🚀 Cierra la función para evitar la recursión infinita

            conexion_ssl.sendall("🔒 Contraseña: ".encode('utf-8'))
            password = conexion_ssl.recv(1024).decode().strip()
            logging.info(f"🔑 Intentando autenticar usuario {usuario}")

            datos_usuario = autenticar_usuario_en_servidor(usuario, password)
            if not datos_usuario:
                conexion_ssl.sendall("❌ Credenciales inválidas. Intenta nuevamente.\n".encode('utf-8'))
                continue  # Permitir que el usuario lo intente de nuevo

            usuario_id, permisos = datos_usuario
            conexion_ssl.sendall(f"✅ Autenticación exitosa! Permisos: {permisos}\n".encode('utf-8'))
            logging.info(f"✅ Usuario {usuario} autenticado con permisos: {permisos}")
            break  # Sale del bucle de autenticación y continúa con los comandos

        # Bucle para procesar comandos del usuario autenticado
        while True:
            conexion_ssl.sendall("\n💻 Ingresar comando ('SALIR' para desconectar): ".encode('utf-8'))
            comando = conexion_ssl.recv(1024).decode().strip()
            logging.info(f"📥 Comando recibido: {comando}")

            if comando.upper() == "SALIR":
                conexion_ssl.sendall("🔌 Desconectando...\n".encode('utf-8'))
                break

            respuesta = manejar_comando(comando, DIRECTORIO_BASE, usuario_id)
            conexion_ssl.sendall(f"📄 {respuesta}\n".encode('utf-8'))

    except Exception as e:
        logging.error(f"❌ Error con cliente {direccion}: {e}")
    finally:
        conexion_ssl.close()
        logging.info(f"🔌 Conexión cerrada con {direccion}")


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
        logging.error(f"❌ Error: No se encontraron los certificados en {cert_path} o {key_path}.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((HOST, PORT))
        servidor.listen(5)
        logging.info(f"✅ Servidor escuchando en {HOST}:{PORT}")

        while True:
            conexion, direccion = servidor.accept()
            try:
                conexion_ssl = contexto.wrap_socket(conexion, server_side=True)
                threading.Thread(target=manejar_cliente, args=(conexion_ssl, direccion)).start()
            except ssl.SSLError as e:
                logging.error(f"❌ Error SSL con {direccion}: {e}")
                conexion.close()


if __name__ == "__main__":
    iniciar_servidor()
