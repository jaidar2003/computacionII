import socket
from ..utils import config
from ..utils.config import actualizar_configuracion, validar_direccion_ip
from ..utils.visual import (
    print_success, print_error, print_info, print_warning, print_header,
    format_success, format_error, format_info, format_warning, BOLD, RESET
)

def update_server_ip(new_ip=None, new_port=None):
    """Actualiza la configuración del servidor en el archivo .env
    
    Args:
        new_ip (str, optional): Nueva dirección IP o hostname. Si no se proporciona, se solicitará.
        new_port (str, optional): Nuevo puerto. Si no se proporciona, se mantendrá el actual.
    """
    print_header("CONFIGURACIÓN DEL SERVIDOR")
    
    # Mostrar la configuración actual
    print_info(f"Configuración actual:")
    print(f"  Servidor: {BOLD}{config.SERVER_HOST}{RESET}")
    print(f"  Puerto: {BOLD}{config.SERVER_PORT}{RESET}")
    
    # Si no se proporcionó una IP, intentar detectarla o solicitarla
    if not new_ip:
        print_info("No se proporcionó una nueva dirección IP. Intentando detectar automáticamente...")
        try:
            # Intentar obtener la IP del servidor mediante resolución de nombres
            # Intentar primero con IPv6, luego con IPv4
            try:
                ip_info = socket.getaddrinfo(config.SERVER_HOST, config.SERVER_PORT, socket.AF_INET6, socket.SOCK_STREAM)
                if ip_info:
                    detected_ip = ip_info[0][4][0]
                    ip_type = "IPv6"
                else:
                    raise socket.gaierror("No se encontró información IPv6")
            except (socket.gaierror, socket.error):
                # Intentar con IPv4
                try:
                    ip_info = socket.getaddrinfo(config.SERVER_HOST, config.SERVER_PORT, socket.AF_INET, socket.SOCK_STREAM)
                    if ip_info:
                        detected_ip = ip_info[0][4][0]
                        ip_type = "IPv4"
                    else:
                        raise socket.gaierror("No se encontró información IPv4")
                except (socket.gaierror, socket.error):
                    print_warning(f"No se pudo detectar la IP para {config.SERVER_HOST}")
                    detected_ip = None
                    ip_type = "desconocido"
            
            if detected_ip:
                print_info(f"IP detectada para {config.SERVER_HOST}: {BOLD}{detected_ip}{RESET} ({ip_type})")
                
                # Preguntar si se desea usar esta IP
                response = input(f"¿Deseas usar esta IP? (s/n): ").lower()
                if response in ['s', 'si', 'y', 'yes']:
                    new_ip = detected_ip
                else:
                    # Solicitar la nueva IP manualmente
                    new_ip = input("Ingresa la nueva dirección IP o hostname del servidor: ")
            else:
                new_ip = input("Ingresa la nueva dirección IP o hostname del servidor: ")
        except Exception as e:
            print_warning(f"Error al detectar IP: {str(e)}")
            new_ip = input("Ingresa la nueva dirección IP o hostname del servidor: ")
    
    # Si no se proporcionó un puerto, preguntar si se desea cambiar
    if not new_port:
        change_port = input(f"¿Deseas cambiar el puerto actual ({BOLD}{config.SERVER_PORT}{RESET})? (s/n): ").lower()
        if change_port in ['s', 'si', 'y', 'yes']:
            while True:
                new_port = input(f"Ingresa el nuevo puerto del servidor [1608]: ").strip() or "1608"
                try:
                    port_num = int(new_port)
                    if 1 <= port_num <= 65535:
                        break
                    else:
                        print_error(f"El puerto debe estar entre 1 y 65535.")
                except ValueError:
                    print_error(f"El puerto debe ser un número entero.")
    
    # Validar la IP ingresada si no es un hostname conocido
    if new_ip.lower() not in ["localhost", "127.0.0.1", "::1"]:
        es_valida, tipo_ip = validar_direccion_ip(new_ip)
        if not es_valida:
            print_error(f"La dirección IP {BOLD}{new_ip}{RESET} no es válida")
            print_info("Ingresa una dirección IPv4 (ej: 192.168.1.10) o IPv6 (ej: 2001:db8::1)")
            return
        else:
            print_info(f"Dirección {tipo_ip} válida: {BOLD}{new_ip}{RESET}")
    
    # Actualizar la configuración en el archivo .env
    if actualizar_configuracion(new_ip, new_port):
        print_success(f"Configuración actualizada correctamente:")
        print(f"  Servidor: {BOLD}{new_ip}{RESET}")
        if new_port:
            print(f"  Puerto: {BOLD}{new_port}{RESET}")
        else:
            print(f"  Puerto: {BOLD}{cli.utils.config.SERVER_PORT}{RESET} (sin cambios)")
        print_info("Reinicia la aplicación para aplicar los cambios.")
    else:
        print_error("No se pudo actualizar la configuración en el archivo .env")