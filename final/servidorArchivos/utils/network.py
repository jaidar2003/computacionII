import socket
import logging
import ssl
import os

def crear_socket_servidor(host, port, return_socket=True):
    # Obtener información de direcciones para IPv4 e IPv6
    addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)

    # Intentar crear socket con cada familia de direcciones
    for family, socktype, proto, canonname, sockaddr in addr_info:
        try:
            servidor = socket.socket(family, socktype, proto)
            servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            servidor.bind(sockaddr)
            servidor.listen(5)

            logging.info(f"✅ Servidor iniciado en {sockaddr[0]}:{sockaddr[1]} ({family})")

            if return_socket:
                return servidor
            else:
                return True

        except OSError as e:
            logging.warning(f"No se pudo iniciar servidor con familia {family}: {e}")
            if 'servidor' in locals():
                servidor.close()
            continue

    # Si llegamos aquí, no pudimos crear ningún socket
    raise OSError("No se pudo crear un socket para escuchar conexiones")

def configurar_contexto_ssl(cert_path, key_path):
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logging.error(f"❌ ERROR: No se encontraron los certificados SSL en {cert_path} o {key_path}.")
        return None

    contexto.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return contexto
