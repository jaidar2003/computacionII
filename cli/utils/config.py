import os
import json

# Directorio de configuración
CONFIG_DIR = os.path.expanduser("~/.file-server-cli")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Archivo de sesión
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")

# URL base de la API
API_URL = "http://localhost:5000/api"  # Ajustar según la configuración del servidor