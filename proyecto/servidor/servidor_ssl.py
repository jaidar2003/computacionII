import os
import socket
import ssl
import threading
import logging
import hashlib

# Configuración de Logs
logging.basicConfig(filename="server.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Configuración del servidor
HOST = '127.0.0.1'  # Dirección local
PORT = 5000
DIRECTORIO_BASE = "archivos_servidor"

# Autenticación básica: usuarios permitidos
USUARIOS = {
    "usuario1": hashlib.sha256("password1".encode()).hexdigest(),
    "usuario2": hashlib.sha256("password2".encode()).hexdigest()
}

# Asegurar el directorio base
if not os.path.exists(DIRECTORIO_BASE):
    os.makedirs(DIRECTORIO_BASE)

# Función para manejar clientes
def manejar_cliente(conexion_ssl, direccion):
    try:
        logging.info(f"Conexión aceptada desde {direccion}")
        conexion_ssl.sendall(b"Bienvenido al servidor. Autenticación requerida.\nUsuario: ")
        usuario = conexion_ssl.recv(1024).decode().strip()
        conexion_ssl.sendall(b"Contraseña: ")
        password = conexion_ssl.recv(1024).decode().strip()

        # Verificar credenciales
        if usuario in USUARIOS and USUARIOS[usuario] == hashlib.sha256(password.encode()).hexdigest():
            conexion_ssl.sendall(b"Autenticación exitosa!\n")
            logging.info(f"Usuario autenticado: {usuario}")
        else:
            conexion_ssl.sendall(b"Credenciales inválidas. Desconectando.\n")
            logging.warning(f"Intento fallido de autenticación desde {direccion}")
            conexion_ssl.close()
            return

        while True:
            mensaje = b"\nComandos: LISTAR | CREAR <nombre> | ELIMINAR <nombre> | RENOMBRAR <viejo> <nuevo> | SALIR\n> "
            conexion_ssl.sendall(mensaje)
            comando = conexion_ssl.recv(1024).decode().strip()

            if not comando:
                break

            partes = comando.split()
            accion = partes[0].upper()

            if accion == "LISTAR":
                archivos = os.listdir(DIRECTORIO_BASE)
                conexion_ssl.sendall("\n".join(archivos).encode() or b"No hay archivos.\n")

            elif accion == "CREAR" and len(partes) == 2:
                ruta = os.path.join(DIRECTORIO_BASE, partes[1])
                with open(ruta, "w") as archivo:
                    archivo.write("")  # Crear un archivo vacío
                conexion_ssl.sendall(b"Archivo creado.\n")
                logging.info(f"Archivo creado: {partes[1]}")

            elif accion == "ELIMINAR" and len(partes) == 2:
                ruta = os.path.join(DIRECTORIO_BASE, partes[1])
                if os.path.exists(ruta):
                    os.remove(ruta)
                    conexion_ssl.sendall(b"Archivo eliminado.\n")
                    logging.info(f"Archivo eliminado: {partes[1]}")
                else:
                    conexion_ssl.sendall(b"Archivo no encontrado.\n")

            elif accion == "RENOMBRAR" and len(partes) == 3:
                viejo = os.path.join(DIRECTORIO_BASE, partes[1])
                nuevo = os.path.join(DIRECTORIO_BASE, partes[2])
                if os.path.exists(viejo):
                    os.rename(viejo, nuevo)
                    conexion_ssl.sendall(b"Archivo renombrado.\n")
                    logging.info(f"Archivo renombrado: {partes[1]} a {partes[2]}")
                else:
                    conexion_ssl.sendall(b"Archivo no encontrado.\n")

            elif accion == "SALIR":
                conexion_ssl.sendall(b"Desconectando...\n")
                logging.info(f"Usuario desconectado: {usuario}")
                break

            else:
                conexion_ssl.sendall(b"Comando no reconocido.\n")

    except Exception as e:
        logging.error(f"Error con cliente {direccion}: {e}")
    finally:
        conexion_ssl.close()
        logging.info(f"Conexión cerrada con {direccion}")

# Servidor principal
def iniciar_servidor():
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    contexto.load_cert_chain(certfile="certificado.pem", keyfile="llave.pem")  # Genera tus propios certificados

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