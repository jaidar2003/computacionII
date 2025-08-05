import socket
import logging
import ssl
import os

def crear_socket_servidor(host, port, return_socket=True):
    # Validar la dirección IP antes de continuar
    try:
        # Intentar validar la dirección IP
        socket.inet_aton(host)
    except socket.error:
        # Si no es una dirección IPv4 válida, verificar si es un nombre de host válido
        try:
            socket.gethostbyname(host)
        except socket.gaierror:
            # No es una dirección IP válida ni un nombre de host válido
            raise OSError(f"No se pudo crear un socket para escuchar conexiones: Dirección IP inválida '{host}'")
    
    try:
        # Obtener información de direcciones para IPv4 e IPv6
        addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        # Error al resolver la dirección
        raise OSError(f"No se pudo crear un socket para escuchar conexiones: No se puede resolver la dirección '{host}'")
    
    # Lista para almacenar los sockets creados exitosamente
    sockets_creados = []

    # Intentar crear socket con cada familia de direcciones
    for family, socktype, proto, canonname, sockaddr in addr_info:
        try:
            servidor = socket.socket(family, socktype, proto)
            servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # En IPv6, habilitar la opción para permitir conexiones IPv4 e IPv6 en el mismo socket
            if family == socket.AF_INET6:
                servidor.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

            servidor.bind(sockaddr)
            servidor.listen(5)

            logging.info(f"✅ Servidor iniciado en {sockaddr[0]}:{sockaddr[1]} ({family})")

            # Agregar el socket a la lista de sockets creados
            sockets_creados.append(servidor)

            # Si solo queremos verificar si se puede crear un socket, retornar True
            if not return_socket:
                # Cerrar el socket ya que solo queríamos verificar
                servidor.close()
                return True

        except OSError as e:
            logging.warning(f"No se pudo iniciar servidor con familia {family}: {e}")
            if 'servidor' in locals():
                servidor.close()
            continue

    # Verificar si se creó al menos un socket
    if sockets_creados:
        if return_socket:
            return sockets_creados
        else:
            return True
    else:
        # Si llegamos aquí, no pudimos crear ningún socket
        raise OSError("No se pudo crear un socket para escuchar conexiones")

def configurar_contexto_ssl(cert_path, key_path):
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logging.error(f"❌ ERROR: No se encontraron los certificados SSL en {cert_path} o {key_path}.")
        return None

    contexto.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return contexto
