#!/usr/bin/env python3
import socket
import threading
import sys
import os
import argparse

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

def handle_client(client_socket, addr):
    """Handles a client connection"""
    protocol = "IPv6" if ":" in addr[0] else "IPv4"
    print(f"✅ Conexión establecida desde {addr[0]} ({protocol})")
    
    try:
        # Send welcome message
        client_socket.send(f"¡Hola! Te has conectado al servidor usando {protocol}\n".encode('utf-8'))
        
        # Receive data from client
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data or data.lower() == 'salir':
                break
                
            # Send response
            response = f"Recibido: {data}"
            client_socket.send(response.encode('utf-8'))
            print(f"Mensaje de {addr[0]}: {data}")
    
    except Exception as e:
        print(f"Error con cliente {addr[0]}: {e}")
    finally:
        client_socket.close()
        print(f"🔌 Conexión cerrada con {addr[0]} ({protocol})")

def accept_connections(server_socket, protocol):
    """Accepts connections on a specific socket"""
    print(f"👂 Esperando conexiones {protocol}...")
    
    while True:
        try:
            client, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client, addr))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            print(f"❌ Error al aceptar conexión {protocol}: {e}")
            break

def start_server(port=5005, verbose=False):
    """Starts a dual stack server that listens on IPv4 and IPv6"""
    # Get local IP addresses
    ipv4_addr = obtener_ip_local()
    ipv6_addr = obtener_ipv6_local()
    
    print("📡 Información de red local")
    print("-" * 30)
    print(f"🧩 Dirección IPv4 local: {ipv4_addr}")
    print(f"🧬 Dirección IPv6 local: {ipv6_addr}")
    print("-" * 30)
    
    # Create IPv4 socket
    ipv4_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ipv4_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Create IPv6 socket
    ipv6_server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    ipv6_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ipv6_server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)  # IPv6 only
    
    active_sockets = []
    
    try:
        # Bind sockets to all interfaces
        try:
            ipv4_server.bind(('0.0.0.0', port))
            ipv4_server.listen(5)
            active_sockets.append(('IPv4', ipv4_server))
            print(f"✅ Socket IPv4 escuchando en 0.0.0.0:{port} (accesible en {ipv4_addr}:{port})")
        except Exception as e:
            print(f"❌ No se pudo iniciar el socket IPv4: {e}")
            ipv4_server.close()
            ipv4_server = None
        
        try:
            ipv6_server.bind(('::', port))
            ipv6_server.listen(5)
            active_sockets.append(('IPv6', ipv6_server))
            print(f"✅ Socket IPv6 escuchando en [::]:{port} (accesible en [{ipv6_addr}]:{port})")
        except Exception as e:
            print(f"❌ No se pudo iniciar el socket IPv6: {e}")
            ipv6_server.close()
            ipv6_server = None
        
        if not active_sockets:
            print("❌ No se pudo iniciar ningún socket. Verifica tu configuración de red.")
            return
        
        print(f"🌍 Servidor escuchando en puerto {port} ({len(active_sockets)} interfaces)")
        
        # Threads for accepting connections
        threads = []
        for protocol, sock in active_sockets:
            thread = threading.Thread(target=accept_connections, args=(sock, protocol), daemon=True)
            threads.append(thread)
            thread.start()
        
        # Keep the program running
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            print("\n👋 Servidor detenido por el usuario")
        
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
    finally:
        # Close all sockets
        if ipv4_server:
            ipv4_server.close()
        if ipv6_server:
            ipv6_server.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor de prueba para dual stack (IPv4 + IPv6)")
    parser.add_argument("-p", "--port", type=int, default=5005, help="Puerto para escuchar (default: 5005)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar mensajes detallados")
    args = parser.parse_args()
    
    start_server(port=args.port, verbose=args.verbose)