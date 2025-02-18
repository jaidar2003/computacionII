from bd import autenticar_usuario, registrar_usuario
import hashlib

# Diccionario de usuarios y contraseñas (las contraseñas deben ser almacenadas de manera segura en producción)
USUARIOS = {
    "juanma": hashlib.sha256("45143375".encode()).hexdigest(),
    "usuario": hashlib.sha256("password".encode()).hexdigest()
}

def autenticar_usuario(usuario, password):
    """
    Autentica a un usuario comparando su nombre de usuario y contraseña (encriptada) con los valores almacenados.
    """
    if usuario in USUARIOS:
        password_encriptada = hashlib.sha256(password.encode()).hexdigest()
        if USUARIOS[usuario] == password_encriptada:
            return True
    return False

def crear_contexto_ssl(certfile, keyfile):
    """
    Crea y configura un contexto SSL para el servidor, utilizando los certificado proporcionados.
    """
    import ssl
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    contexto.load_cert_chain(certfile=certfile, keyfile=keyfile)
    return contexto


def autenticar_usuario_en_servidor(username, password):
    """Autentica al usuario usando la base de datos."""
    usuario = autenticar_usuario(username, password)
    if usuario:
        return usuario  # Devuelve (id, permisos)
    return None


def manejar_cliente(conexion_ssl, direccion):
    try:
        conexion_ssl.sendall("Bienvenido al servidor. Autenticación requerida.\nUsuario: ".encode('utf-8'))
        usuario = conexion_ssl.recv(1024).decode().strip()
        conexion_ssl.sendall("Contraseña: ".encode('utf-8'))
        password = conexion_ssl.recv(1024).decode().strip()

        datos_usuario = autenticar_usuario_en_servidor(usuario, password)
        if not datos_usuario:
            conexion_ssl.sendall("Credenciales inválidas. Desconectando.\n".encode('utf-8'))
            return

        usuario_id, permisos = datos_usuario
        conexion_ssl.sendall(f"Autenticación exitosa! Permisos: {permisos}\n".encode('utf-8'))

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
