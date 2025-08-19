import socket
import psutil

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except Exception as e:
        return f"❌ Error al obtener IPv4 local: {e}"


def obtener_ipv6_local():
    # Primero intentar encontrar una dirección IPv6 global (no link-local)
    direccion_global = None
    direccion_link_local = None

    for interfaz, direcciones in psutil.net_if_addrs().items():
        # Saltar interfaces de loopback
        if interfaz.startswith('lo'):
            continue

        for direccion in direcciones:
            if direccion.family == socket.AF_INET6:
                ip = direccion.address

                # Verificar si es una dirección global (no comienza con fe80)
                if not ip.startswith("fe80"):
                    return ip  # Retornar inmediatamente si encontramos una dirección global
                elif not direccion_link_local:
                    # Guardar la primera dirección link-local como respaldo
                    direccion_link_local = ip

    # Si encontramos una dirección link-local de una interfaz no-loopback, usarla
    if direccion_link_local:
        return direccion_link_local

    # Si no encontramos nada, buscar en todas las interfaces (incluyendo loopback)
    for interfaz, direcciones in psutil.net_if_addrs().items():
        for direccion in direcciones:
            if direccion.family == socket.AF_INET6:
                return direccion.address

    return "⚠️ No se encontró una dirección IPv6."
if __name__ == "__main__":
    ipv4 = obtener_ip_local()
    ipv6 = obtener_ipv6_local()

    print("📡 Información de red local")
    print("-" * 30)
    print(f"🧩 Dirección IPv4 local: \033[92m{ipv4}\033[0m")
    print(f"🧬 Dirección IPv6 local: \033[94m{ipv6}\033[0m")