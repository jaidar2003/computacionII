#!/usr/bin/env python3
import socket
import sys
import os
import argparse
import time

# Add the project directory to the path to import IP utility functions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from final.servidorArchivos.utils.ip import obtener_ip_local, obtener_ipv6_local
except ImportError:
    # Fallback implementation if the import fails
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
        try:
            import psutil
            # First try to find a global IPv6 address (not link-local)
            global_addr = None
            link_local_addr = None
            
            for interface, addrs in psutil.net_if_addrs().items():
                # Skip loopback interfaces
                if interface.startswith('lo'):
                    continue
                    
                for addr in addrs:
                    if getattr(addr, 'family', None) == socket.AF_INET6:
                        ip = addr.address
                        
                        # Check if it's a global address (not starting with fe80)
                        if not ip.startswith("fe80"):
                            return ip  # Return immediately if we find a global address
                        elif not link_local_addr:
                            # Save the first link-local address as a fallback
                            link_local_addr = ip
            
            # If we found a link-local address from a non-loopback interface, use it
            if link_local_addr:
                return link_local_addr
                
            # If we didn't find anything, look in all interfaces (including loopback)
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if getattr(addr, 'family', None) == socket.AF_INET6:
                        return addr.address
                        
            return "⚠️ No se encontró una dirección IPv6."
        except ImportError:
            return "⚠️ No se pudo importar psutil para obtener IPv6."
        except Exception as e:
            return f"❌ Error al obtener IPv6 local: {e}"

def connect_to_server(host, port=5005, use_ipv6=False, timeout=10):
    """Connects to the server using IPv4 or IPv6"""
    try:
        # Create socket of the appropriate type
        if use_ipv6:
            client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            protocol = "IPv6"
        else:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            protocol = "IPv4"
        
        # Set timeout for connection attempts
        client.settimeout(timeout)
        
        print(f"🔌 Conectando a {host}:{port} usando {protocol}...")
        start_time = time.time()
        client.connect((host, port))
        connect_time = time.time() - start_time
        
        print(f"✅ Conexión establecida en {connect_time:.3f} segundos")
        
        # Receive welcome message
        welcome = client.recv(1024).decode('utf-8')
        print(f"🌍 {welcome}")
        
        # Interaction loop
        while True:
            message = input("Mensaje (o 'salir' para terminar): ")
            if message.lower() == 'salir':
                client.send(message.encode('utf-8'))
                break
                
            client.send(message.encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            print(f"📩 Respuesta: {response}")
            
    except ConnectionRefusedError:
        print(f"❌ Conexión rechazada. Verifica que el servidor esté en ejecución y que {protocol} esté permitido.")
        print("   Si el servidor está en ejecución, es posible que un firewall esté bloqueando la conexión.")
    except socket.timeout:
        print(f"❌ Tiempo de espera agotado al intentar conectar usando {protocol}.")
        print("   Esto puede indicar un problema de firewall o que el servidor no está escuchando en esa dirección.")
    except socket.gaierror:
        print(f"❌ Error de resolución de dirección. Verifica que la dirección {host} sea válida para {protocol}.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            client.close()
        except:
            pass
        print("🔌 Conexión cerrada")

def main():
    parser = argparse.ArgumentParser(description="Cliente de prueba para dual stack (IPv4 + IPv6)")
    parser.add_argument("-4", "--ipv4", action="store_true", help="Usar IPv4")
    parser.add_argument("-6", "--ipv6", action="store_true", help="Usar IPv6")
    parser.add_argument("-H", "--host", type=str, help="Dirección del servidor")
    parser.add_argument("-p", "--port", type=int, default=5005, help="Puerto del servidor (default: 5005)")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Tiempo de espera en segundos (default: 10)")
    args = parser.parse_args()
    
    # Get local IP addresses
    ipv4_addr = obtener_ip_local()
    ipv6_addr = obtener_ipv6_local()
    
    print("📡 Información de red local")
    print("-" * 30)
    print(f"🧩 Dirección IPv4 local: {ipv4_addr}")
    print(f"🧬 Dirección IPv6 local: {ipv6_addr}")
    print("-" * 30)
    
    # Determine protocol and host
    if args.host:
        host = args.host
        # Determine if it's an IPv6 address
        use_ipv6 = ":" in host
    else:
        if args.ipv4 and args.ipv6:
            print("❌ No puedes especificar tanto IPv4 como IPv6 al mismo tiempo.")
            return
        
        if args.ipv6:
            use_ipv6 = True
            default_host = ipv6_addr if ipv6_addr and not ipv6_addr.startswith("⚠️") else "::1"
        else:  # Default to IPv4
            use_ipv6 = False
            default_host = ipv4_addr if ipv4_addr and not ipv4_addr.startswith("❌") else "127.0.0.1"
            
        # Ask for server address
        host = input(f"Dirección {'IPv6' if use_ipv6 else 'IPv4'} del servidor [{default_host}]: ") or default_host
    
    # Connect to the server
    connect_to_server(host, args.port, use_ipv6=(":" in host), timeout=args.timeout)

if __name__ == "__main__":
    main()