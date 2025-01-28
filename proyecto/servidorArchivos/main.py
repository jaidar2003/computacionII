from comandos import manejar_comando
from seguridad import autenticar_usuario, crear_contexto_ssl

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
