import os
import json

# Directorio de configuración
CONFIG_DIR = os.path.expanduser("~/.file-server-cli")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Archivo de sesión
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")

# Configuración del servidor
SERVER_HOST = "127.0.0.1"  # Dirección IPv4 loopback (funciona en cualquier sistema)
SERVER_PORT = 5005  # Puerto del servidor
