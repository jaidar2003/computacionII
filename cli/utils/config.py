import os
import json
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorio de configuración
CONFIG_DIR = os.path.expanduser("~/.file-server-cli")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Archivo de sesión
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")

# Configuración del servidor
SERVER_HOST = os.getenv("SERVER_HOST", "192.168.100.142")  # Usar valor de .env o valor por defecto
SERVER_PORT = int(os.getenv("SERVER_PORT", "5005"))  # Usar valor de .env o valor por defecto

def actualizar_ip_en_env(nueva_ip):
    """Actualiza la dirección IP del servidor en el archivo .env"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    # Si el archivo no existe, crearlo
    if not os.path.exists(env_path):
        with open(env_path, 'w') as file:
            file.write(f"SERVER_HOST={nueva_ip}\nSERVER_PORT={SERVER_PORT}\n")
        return True
    
    # Leer el contenido actual del archivo .env
    with open(env_path, 'r') as file:
        contenido = file.read()
    
    # Reemplazar la IP actual con la nueva IP
    patron = r'SERVER_HOST=.*'
    if re.search(patron, contenido):
        nuevo_contenido = re.sub(patron, f'SERVER_HOST={nueva_ip}', contenido)
    else:
        nuevo_contenido = contenido + f'\nSERVER_HOST={nueva_ip}'
    
    # Escribir el nuevo contenido al archivo .env
    with open(env_path, 'w') as file:
        file.write(nuevo_contenido)
    
    return True
