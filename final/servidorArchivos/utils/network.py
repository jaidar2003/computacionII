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
            servidor_v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            servidor_v6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                # separa pilas: sin IPv4-mapped
                servidor_v6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except OSError:
                pass

            bind_ok = False

            # Mapeos rápidos si el host viene en notación IPv4
            if host == "0.0.0.0":
                sockaddr = ("::", port)
                servidor_v6.bind(sockaddr)
                bind_ok = True
            elif host == "127.0.0.1":
                sockaddr = ("::1", port)
                servidor_v6.bind(sockaddr)
                bind_ok = True
            else:
                # Resolver y probar TODAS las direcciones, filtrando AF_INET6
                try:
                    addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                except socket.gaierror:
                    addr_list = []

                for family, socktype, proto, canon, sockaddr in addr_list:
                    if family != socket.AF_INET6:
                        continue
                    try:
                        servidor_v6.bind(sockaddr)
                        bind_ok = True
                        break
                    except OSError:
                        continue

            if bind_ok:
                servidor_v6.listen(128)
                try:
                    bound = servidor_v6.getsockname()
                    logging.info(f"✅ Servidor IPv6 iniciado en [{bound[0]}]:{bound[1]}")
                except Exception:
                    logging.info(f"✅ Servidor IPv6 iniciado (bind OK)")
                sockets_creados.append(servidor_v6)
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
            servidor_v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            servidor_v4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            bind_ok = False

            # Mapeos rápidos si el host viene en notación IPv6
            if host == "::":
                sockaddr = ("0.0.0.0", port)
                servidor_v4.bind(sockaddr)
                bind_ok = True
            elif host == "::1":
                sockaddr = ("127.0.0.1", port)
                servidor_v4.bind(sockaddr)
                bind_ok = True
            else:
                # Resolver y probar TODAS las direcciones, filtrando AF_INET
                try:
                    addr_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                except socket.gaierror:
                    addr_list = []

                for family, socktype, proto, canon, sockaddr in addr_list:
                    if family != socket.AF_INET:
                        continue
                    try:
                        servidor_v4.bind(sockaddr)
                        bind_ok = True
                        break
                    except OSError:
                        continue

            if bind_ok:
                servidor_v4.listen(128)
                try:
                    bound = servidor_v4.getsockname()
                    logging.info(f"✅ Servidor IPv4 iniciado en {bound[0]}:{bound[1]}")
                except Exception:
                    logging.info(f"✅ Servidor IPv4 iniciado (bind OK)")
                sockets_creados.append(servidor_v4)
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
        s4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s4.bind(('0.0.0.0', 0))
        s4.close()
        stack_disponible['ipv4'] = True
        logging.info("✅ Stack IPv4 (0.0.0.0) disponible")
    except OSError as e:
        logging.warning(f"❌ Stack IPv4 no disponible: {e}")

    # IPv6
    try:
        s6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            s6.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        except OSError:
            pass
        s6.bind(('::', 0))
        s6.close()
        stack_disponible['ipv6'] = True
        logging.info("✅ Stack IPv6 (::) disponible")
    except OSError as e:
        logging.warning(f"❌ Stack IPv6 no disponible: {e}")

    # 📢 Resumen final
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
    contexto = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logging.error(f"❌ ERROR: No se encontraron los certificados SSL en {cert_path} o {key_path}.")
        return None
    contexto.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return contexto
