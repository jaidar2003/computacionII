import socket
import logging
import ssl
import os

def crear_socket_servidor(host, port, return_socket=True, stack_disponible=None):
    sockets_creados = []
    servidor_v6 = None
    servidor_v4 = None

    # Fallback si no pasan disponibilidad: intentamos ambos por defecto
    if stack_disponible is None:
        stack_disponible = {'ipv4': True, 'ipv6': True}

    # IPv6

    if stack_disponible.get('ipv6', True):
        try:
            servidor_v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM) #IPV6 TCP
            servidor_v6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Habilita reusar dirección
            try:
                # Separa pilas IPv4/IPv6: evita mapear IPv4 en IPv6
                servidor_v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except OSError:
                pass  # Algunos sistemas no soportan esta opción

            bind_ok = False

            # Mapeos rápidos de direcciones IPv4 a IPv6
            if host == "0.0.0.0":
                sockaddr = ("::", port)  # 0.0.0.0 -> :: (cualquier dirección IPv6)
                servidor_v6.bind(sockaddr)
                bind_ok = True
            elif host == "127.0.0.1":
                sockaddr = ("::1", port)  # 127.0.0.1 -> ::1 (loopback IPv6)
                servidor_v6.bind(sockaddr)
                bind_ok = True
            else:
                # Resolver hostname a direcciones IP usando getaddrinfo
                try:
                    addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                except socket.gaierror:
                    addr_list = []  # Si falla la resolución, lista vacía

                # Probar todas las direcciones IPv6 hasta encontrar una que funcione
                for family, socktype, proto, canon, sockaddr in addr_list:
                    if family != socket.AF_INET6:
                        continue  # Solo procesamos direcciones IPv6
                    try:
                        servidor_v6.bind(sockaddr)  # Intentar bind a esta dirección
                        bind_ok = True
                        break  # Si funciona, salir del bucle
                    except OSError:
                        continue  # Si falla, probar la siguiente dirección

            if bind_ok:
                servidor_v6.listen(128)  # Activar modo listening con cola de 128 conexiones
                try:
                    bound = servidor_v6.getsockname()  # Obtener dirección real asignada
                    logging.info(f"✅ Servidor IPv6 iniciado en [{bound[0]}]:{bound[1]}")
                except Exception:
                    logging.info(f"✅ Servidor IPv6 iniciado (bind OK)")
                sockets_creados.append(servidor_v6)  # Agregar socket a la lista
                if not return_socket:
                    servidor_v6.close()
                    return True
            else:
                if servidor_v6:
                    servidor_v6.close()
                servidor_v6 = None

        except OSError as e:
            logging.warning(f"❌ No se pudo iniciar servidor IPv6: {e}")
            if servidor_v6:
                servidor_v6.close()
                servidor_v6 = None
    else:
        logging.info("ℹ️ Omitiendo socket IPv6 (no disponible)")


    # IPv4

    if stack_disponible.get('ipv4', True):
        try:
            servidor_v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 TCP
            servidor_v4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Habilita reusar dirección

            bind_ok = False

            # Mapeos rápidos de direcciones IPv6 a IPv4
            if host == "::":
                sockaddr = ("0.0.0.0", port)  # :: -> 0.0.0.0 (cualquier dirección IPv4)
                servidor_v4.bind(sockaddr)
                bind_ok = True
            elif host == "::1":
                sockaddr = ("127.0.0.1", port)  # ::1 -> 127.0.0.1 (loopback IPv4)
                servidor_v4.bind(sockaddr)
                bind_ok = True
            else:
                # Resolver hostname a direcciones IP usando getaddrinfo
                try:
                    addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                except socket.gaierror:
                    addr_list = []  # Si falla la resolución, lista vacía

                # Probar todas las direcciones IPv4 hasta encontrar una que funcione
                for family, socktype, proto, canon, sockaddr in addr_list:
                    if family != socket.AF_INET:
                        continue  # Solo procesamos direcciones IPv4
                    try:
                        servidor_v4.bind(sockaddr)  # Intentar bind a esta dirección
                        bind_ok = True
                        break  # Si funciona, salir del bucle
                    except OSError:
                        continue  # Si falla, probar la siguiente dirección

            if bind_ok:
                servidor_v4.listen(128)  # Activar modo listening con cola de 128 conexiones
                try:
                    bound = servidor_v4.getsockname()  # Obtener dirección real asignada
                    logging.info(f"✅ Servidor IPv4 iniciado en {bound[0]}:{bound[1]}")
                except Exception:
                    logging.info(f"✅ Servidor IPv4 iniciado (bind OK)")
                sockets_creados.append(servidor_v4)  # Agregar socket a la lista
                if not return_socket:
                    servidor_v4.close()
                    return True
            else:
                if servidor_v4:
                    servidor_v4.close()
                servidor_v4 = None

        except OSError as e:
            logging.warning(f"❌ No se pudo iniciar servidor IPv4: {e}")
            if servidor_v4:
                servidor_v4.close()
                servidor_v4 = None
    else:
        logging.info("ℹ️ Omitiendo socket IPv4 (no disponible)")

    # Resultado
    if sockets_creados:
        return sockets_creados if return_socket else True
    raise OSError("No se pudo crear un socket para escuchar conexiones")


def verificar_stack():
    stack_disponible = {'ipv4': False, 'ipv6': False}

    # IPv4
    try:
        s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crear socket IPv4 de prueba
        s4.bind(('0.0.0.0', 0))  # Bind a cualquier dirección y puerto aleatorio
        s4.close()  # Cerrar socket de prueba
        stack_disponible['ipv4'] = True  # Marcar IPv4 como disponible
        logging.info("✅ Stack IPv4 (0.0.0.0) disponible")
    except OSError as e:
        logging.warning(f"❌ Stack IPv4 no disponible: {e}")

    # IPv6
    try:
        s6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)  # Crear socket IPv6 de prueba
        try:
            s6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)  # Separar pilas IPv4/IPv6
        except OSError:
            pass  # Ignorar si no se puede configurar
        s6.bind(('::', 0))  # Bind a cualquier dirección IPv6 y puerto aleatorio
        s6.close()  # Cerrar socket de prueba
        stack_disponible['ipv6'] = True  # Marcar IPv6 como disponible
        logging.info("✅ Stack IPv6 (::) disponible")
    except OSError as e:
        logging.warning(f"❌ Stack IPv6 no disponible: {e}")

    # Mostrar resumen de capacidades de red del sistema
    if stack_disponible['ipv4'] and stack_disponible['ipv6']:
        print("🌍 Esta computadora soporta **IPv4 e IPv6** (Dual Stack).")
    elif stack_disponible['ipv4']:
        print("🌍 Esta computadora soporta **solo IPv4**.")
    elif stack_disponible['ipv6']:
        print("🌍 Esta computadora soporta **solo IPv6**.")
    else:
        print("❌ Esta computadora no soporta ni IPv4 ni IPv6 para bind.")

    return stack_disponible


def configurar_contexto_ssl(cert_path, key_path):
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # Crear contexto SSL para servidor
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logging.error(f"❌ ERROR: No se encontraron los certificados SSL en {cert_path} o {key_path}.")
        return None  # Fallar si no existen los certificados
    contexto.load_cert_chain(certfile=cert_path, keyfile=key_path)  # Cargar certificado y clave privada
    return contexto  # Retornar contexto SSL configurado
