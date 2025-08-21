import os
import json
import re
import sys
import socket
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorio de configuración
CONFIG_DIR = os.path.expanduser("~/.file-server-cli")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Archivo de sesión
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")

# Ruta al archivo .env
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# Configuración del servidor - Sin valores hardcodeados
SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = os.getenv("SERVER_PORT")

# Verificar si existe configuración
def verificar_configuracion():
    """Verifica si existe configuración del servidor y la crea si no existe"""
    global SERVER_HOST, SERVER_PORT
    
    # Si no hay configuración, ejecutar asistente de configuración
    if not SERVER_HOST or not SERVER_PORT:
        if not os.path.exists(ENV_PATH):
            print("⚠️ No se encontró configuración del servidor.")
            print("ℹ️ Se ejecutará el asistente de configuración inicial.")
            configuracion_inicial()
            # Recargar variables después de la configuración
            load_dotenv()
            SERVER_HOST = os.getenv("SERVER_HOST")
            SERVER_PORT = os.getenv("SERVER_PORT")
        else:
            print("⚠️ El archivo .env existe pero faltan variables de configuración.")
            print("ℹ️ Ejecuta 'cli.py config-server' para configurar el servidor.")
            sys.exit(1)
    
    # Convertir puerto a entero si existe
    if SERVER_PORT:
        try:
            SERVER_PORT = int(SERVER_PORT)
        except ValueError:
            print(f"⚠️ El puerto configurado '{SERVER_PORT}' no es válido. Debe ser un número.")
            print("ℹ️ Ejecuta 'cli.py config-server' para configurar el servidor.")
            sys.exit(1)

# Ejecutar verificación al importar el módulo
verificar_configuracion()

def validar_direccion_ip(ip):
    """Valida si una dirección IP es válida (IPv4 o IPv6)
    
    Args:
        ip (str): Dirección IP a validar
        
    Returns:
        tuple: (bool, str) - (es_valida, tipo_ip)
    """
    # Verificar si es IPv4
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True, "IPv4"
    except socket.error:
        # No es IPv4, verificar si es IPv6
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True, "IPv6"
        except socket.error:
            # No es IPv6 tampoco
            return False, "desconocido"

def configuracion_inicial():
    """Asistente de configuración inicial interactivo"""
    from cli.utils.visual import print_header, print_info, print_success, print_error, BOLD, RESET
    
    print_header("CONFIGURACIÓN INICIAL DEL SERVIDOR")
    print_info("Vamos a configurar la conexión al servidor de archivos.")
    
    # Solicitar dirección del servidor
    while True:
        server_host = input("\nDirección IP o hostname del servidor [localhost]: ").strip() or "localhost"
        
        # Si es un hostname, no validar como IP
        if server_host.lower() in ["localhost", "127.0.0.1", "::1"]:
            if server_host.lower() == "localhost":
                print_info("Usando localhost (se intentará conectar con IPv4 e IPv6)")
            elif server_host == "127.0.0.1":
                print_info("Usando dirección IPv4 de loopback (127.0.0.1)")
            elif server_host == "::1":
                print_info("Usando dirección IPv6 de loopback (::1)")
            break
        
        # Validar si es una dirección IP válida
        es_valida, tipo_ip = validar_direccion_ip(server_host)
        if es_valida:
            print_info(f"Dirección {tipo_ip} válida: {BOLD}{server_host}{RESET}")
            break
        else:
            print_error(f"La dirección IP {BOLD}{server_host}{RESET} no es válida.")
            print_info("Ingresa una dirección IPv4 (ej: 192.168.1.10) o IPv6 (ej: 2001:db8::1)")
    
    # Solicitar puerto
    while True:
        server_port = input("\nPuerto del servidor [1608]: ").strip() or "1608"
        try:
            port_num = int(server_port)
            if 1 <= port_num <= 65535:
                print_info(f"Puerto válido: {BOLD}{port_num}{RESET}")
                break
            else:
                print_error(f"El puerto debe estar entre 1 y 65535.")
        except ValueError:
            print_error(f"El puerto debe ser un número entero.")
    
    # Guardar configuración
    actualizar_configuracion(server_host, server_port)
    
    print_success("\nConfiguración guardada correctamente.")
    print_info(f"Servidor: {BOLD}{server_host}{RESET}")
    print_info(f"Puerto: {BOLD}{server_port}{RESET}")
    
    return server_host, server_port

def actualizar_ip_en_env(nueva_ip):
    """Actualiza la dirección IP del servidor en el archivo .env
    
    Args:
        nueva_ip (str): Nueva dirección IP o hostname
        
    Returns:
        bool: True si se actualizó correctamente
    """
    return actualizar_configuracion(nueva_ip, None)

def actualizar_configuracion(host=None, port=None):
    """Actualiza la configuración del servidor en el archivo .env
    
    Args:
        host (str, optional): Nueva dirección IP o hostname
        port (str, optional): Nuevo puerto
        
    Returns:
        bool: True si se actualizó correctamente
    """
    # Si no se proporciona ningún valor, no hacer nada
    if host is None and port is None:
        return False
    
    # Si el archivo no existe, crearlo
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'w') as file:
            file.write("# Configuración del servidor\n")
            if host:
                file.write(f"SERVER_HOST={host}\n")
            if port:
                file.write(f"SERVER_PORT={port}\n")
        return True
    
    # Leer el contenido actual del archivo .env
    with open(ENV_PATH, 'r') as file:
        contenido = file.read()
    
    # Actualizar host si se proporciona
    if host:
        patron_host = r'SERVER_HOST=.*'
        if re.search(patron_host, contenido):
            contenido = re.sub(patron_host, f'SERVER_HOST={host}', contenido)
        else:
            contenido += f'\nSERVER_HOST={host}'
    
    # Actualizar puerto si se proporciona
    if port:
        patron_port = r'SERVER_PORT=.*'
        if re.search(patron_port, contenido):
            contenido = re.sub(patron_port, f'SERVER_PORT={port}', contenido)
        else:
            contenido += f'\nSERVER_PORT={port}'
    
    # Escribir el nuevo contenido al archivo .env
    with open(ENV_PATH, 'w') as file:
        file.write(contenido)
    
    return True
