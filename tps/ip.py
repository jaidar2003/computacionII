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
    for interfaz, direcciones in psutil.net_if_addrs().items():
        for direccion in direcciones:
            if direccion.family == socket.AF_INET6:
                ip = direccion.address
                if ip.startswith("fe80"):  # link-local
                    return ip
    return "⚠️ No se encontró una IPv6 link-local."

if __name__ == "__main__":
    ipv4 = obtener_ip_local()
    ipv6 = obtener_ipv6_local()

    print("📡 Información de red local")
    print("-" * 30)
    print(f"🧩 Dirección IPv4 local: \033[92m{ipv4}\033[0m")
    print(f"🧬 Dirección IPv6 local: \033[94m{ipv6}\033[0m")
