
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
    Crea y configura un contexto SSL para el servidor, utilizando los certificados proporcionados.
    """
    import ssl
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    contexto.load_cert_chain(certfile=certfile, keyfile=keyfile)
    return contexto
