import socket
import logging
import ssl
import os

def crear_socket_servidor(host, port, return_socket=True, stack_disponible=None):
    """
    Crea sockets para escuchar conexiones IPv4 e IPv6 según disponibilidad.
    Implementa un enfoque de dual-stack real con sockets separados para cada protocolo.
    
    Args:
        host: Dirección IP o nombre de host para escuchar
        port: Puerto para escuchar
        return_socket: Si es True, retorna los sockets creados; si es False, solo verifica si se pueden crear
        stack_disponible: Diccionario con información de disponibilidad de stacks {'ipv4': bool, 'ipv6': bool}
        
    Returns:
        Lista de sockets creados o True si return_socket es False
    """
    # Lista para almacenar los sockets creados exitosamente
    sockets_creados = []
    
    # Usar información de disponibilidad si se proporciona
    if stack_disponible is None:
        stack_disponible = {'ipv4': True, 'ipv6': True}  # Intentar ambos por defecto
    
    # Crear socket IPv6 si está disponible
    if stack_disponible.get('ipv6', True):
        try:
            # Intentar crear un socket IPv6
            servidor_v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            servidor_v6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Configurar IPV6_V6ONLY=1 para evitar conflictos con el socket IPv4
            try:
                servidor_v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except OSError:
                # Algunos sistemas no soportan esta opción, pero no es crítico
                pass
                
            # Intentar hacer bind a la dirección IPv6
            if host == "0.0.0.0":
                # Si se especificó 0.0.0.0, usar :: para IPv6 (todas las interfaces)
                servidor_v6.bind(("::", port))
            elif host == "127.0.0.1":
                # Si se especificó 127.0.0.1, usar ::1 para IPv6 (loopback)
                servidor_v6.bind(("::1", port))
            else:
                # Intentar usar la dirección proporcionada
                try:
                    # Verificar si es una dirección IPv6 válida
                    socket.inet_pton(socket.AF_INET6, host)
                    servidor_v6.bind((host, port))
                except socket.error:
                    # No es una IPv6 válida, intentar resolver como nombre de host
                    try:
                        addr_info = socket.getaddrinfo(host, port, socket.AF_INET6, socket.SOCK_STREAM)
                        if addr_info:
                            servidor_v6.bind(addr_info[0][4])
                        else:
                            raise socket.error("No se pudo resolver el nombre de host a IPv6")
                    except (socket.gaierror, socket.error):
                        # No se pudo resolver a IPv6, cerrar el socket
                        servidor_v6.close()
                        servidor_v6 = None
            
            # Si llegamos aquí y servidor_v6 no es None, configurar para escuchar
            if servidor_v6:
                servidor_v6.listen(128)
                logging.info(f"✅ Servidor IPv6 iniciado en [::] o [{host}]:{port}")
                sockets_creados.append(servidor_v6)
                
                # Si solo queremos verificar, cerrar y retornar
                if not return_socket:
                    servidor_v6.close()
                    return True
                    
        except OSError as e:
            logging.warning(f"No se pudo iniciar servidor IPv6: {e}")
            if 'servidor_v6' in locals() and servidor_v6:
                servidor_v6.close()
    else:
        logging.info("ℹ️ Omitiendo creación de socket IPv6 porque no está disponible")
    
    # Crear socket IPv4 si está disponible
    if stack_disponible.get('ipv4', True):
        try:
            # Intentar crear un socket IPv4
            servidor_v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            servidor_v4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Intentar hacer bind a la dirección IPv4
            if host == "::":
                # Si se especificó ::, usar 0.0.0.0 para IPv4 (todas las interfaces)
                servidor_v4.bind(("0.0.0.0", port))
            elif host == "::1":
                # Si se especificó ::1, usar 127.0.0.1 para IPv4 (loopback)
                servidor_v4.bind(("127.0.0.1", port))
            else:
                # Intentar usar la dirección proporcionada
                try:
                    # Verificar si es una dirección IPv4 válida
                    socket.inet_pton(socket.AF_INET, host)
                    servidor_v4.bind((host, port))
                except socket.error:
                    # No es una IPv4 válida, intentar resolver como nombre de host
                    try:
                        addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
                        if addr_info:
                            servidor_v4.bind(addr_info[0][4])
                        else:
                            raise socket.error("No se pudo resolver el nombre de host a IPv4")
                    except (socket.gaierror, socket.error):
                        # No se pudo resolver a IPv4, cerrar el socket
                        servidor_v4.close()
                        servidor_v4 = None
            
            # Si llegamos aquí y servidor_v4 no es None, configurar para escuchar
            if servidor_v4:
                servidor_v4.listen(128)
                logging.info(f"✅ Servidor IPv4 iniciado en 0.0.0.0 o {host}:{port}")
                sockets_creados.append(servidor_v4)
                
                # Si solo queremos verificar, cerrar y retornar
                if not return_socket:
                    servidor_v4.close()
                    return True
                    
        except OSError as e:
            logging.warning(f"No se pudo iniciar servidor IPv4: {e}")
            if 'servidor_v4' in locals() and servidor_v4:
                servidor_v4.close()
    else:
        logging.info("ℹ️ Omitiendo creación de socket IPv4 porque no está disponible")

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

def verificar_stack():
    """
    Verifica la disponibilidad de IPv4 (0.0.0.0) e IPv6 (::) en el sistema.
    
    Returns:
        dict: Un diccionario con las claves 'ipv4' e 'ipv6' indicando si cada protocolo está disponible.
    """
    stack_disponible = {
        'ipv4': False,
        'ipv6': False
    }
    
    # Verificar IPv4
    try:
        sock_v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_v4.bind(('0.0.0.0', 0))  # Puerto 0 para que el sistema asigne uno automáticamente
        sock_v4.close()
        stack_disponible['ipv4'] = True
        logging.info("✅ Stack IPv4 (0.0.0.0) disponible")
    except OSError as e:
        logging.warning(f"❌ Stack IPv4 no disponible: {e}")
    
    # Verificar IPv6
    try:
        sock_v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # Configurar IPV6_V6ONLY=1 para evitar conflictos con IPv4
        try:
            sock_v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        except OSError:
            pass
        sock_v6.bind(('::', 0))  # Puerto 0 para que el sistema asigne uno automáticamente
        sock_v6.close()
        stack_disponible['ipv6'] = True
        logging.info("✅ Stack IPv6 (::) disponible")
    except OSError as e:
        logging.warning(f"❌ Stack IPv6 no disponible: {e}")
    
    return stack_disponible
