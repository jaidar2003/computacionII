from flask import Flask, request, jsonify, send_file, render_template, session
from flask_cors import CORS
import os
import sys
import threading
import socket
import ssl
import json
import logging
from functools import wraps

# Add parent directory to path to import from sibling packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from server modules
from server.seguridad import autenticar_usuario, registrar_usuario
from server.comandos.operaciones_archivos import listar_archivos, crear_archivo, descargar_archivo
from utils.config import verificar_configuracion_env, CERT_PATH, KEY_PATH
from utils.network import configurar_contexto_ssl

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../front/dist',
            template_folder='../front/dist')
app.secret_key = os.urandom(24)  # For session management

# Enable CORS for development
CORS(app)

# Verify environment configuration
verificar_configuracion_env()

# Get server configuration from environment
SERVER_HOST = os.getenv("SERVIDOR_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVIDOR_PORT", 1608))
SERVER_DIR = os.getenv("SERVIDOR_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archivos"))

# Socket connection cache
socket_connections = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_socket_connection():
    """Get or create a socket connection to the file server"""
    thread_id = threading.get_ident()

    if thread_id in socket_connections:
        return socket_connections[thread_id]

    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure SSL context
        context = configurar_contexto_ssl(CERT_PATH, KEY_PATH, is_client=True)
        if not context:
            raise Exception("Failed to configure SSL context")

        # Wrap socket with SSL
        ssl_sock = context.wrap_socket(sock, server_hostname=SERVER_HOST)

        # Connect to server
        ssl_sock.connect((SERVER_HOST, SERVER_PORT))

        # Store connection in cache
        socket_connections[thread_id] = ssl_sock

        return ssl_sock
    except Exception as e:
        logging.error(f"Error connecting to server: {e}")
        raise

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'usuario' in session:
        return jsonify({"authenticated": True, "usuario": session['usuario']})
    else:
        return jsonify({"authenticated": False}), 401

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña son requeridos"}), 400

    try:
        # Authenticate user through socket connection
        sock = get_socket_connection()

        # Send authentication command
        command = f"AUTH {username} {password}"
        sock.send(command.encode())

        # Receive response
        response = sock.recv(1024).decode()

        if response.startswith("OK"):
            session['usuario'] = username
            return jsonify({"message": "Login exitoso", "usuario": username})
        else:
            return jsonify({"error": "Credenciales inválidas"}), 401
    except Exception as e:
        logging.error(f"Error en login: {e}")
        return jsonify({"error": "Error de conexión al servidor"}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Handle user registration"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña son requeridos"}), 400

    try:
        # Register user through socket connection
        sock = get_socket_connection()

        # Send registration command
        command = f"REGISTER {username} {password}"
        sock.send(command.encode())

        # Receive response
        response = sock.recv(1024).decode()

        if response.startswith("OK"):
            return jsonify({"message": "Registro exitoso"})
        else:
            return jsonify({"error": "Error en el registro: " + response}), 400
    except Exception as e:
        logging.error(f"Error en registro: {e}")
        return jsonify({"error": "Error de conexión al servidor"}), 500

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    """List files in the user's directory"""
    try:
        # Get files through socket connection
        sock = get_socket_connection()

        # Send list command
        command = f"LIST"
        sock.send(command.encode())

        # Receive response
        response = sock.recv(4096).decode()

        if response.startswith("OK"):
            # Parse file list from response
            files_data = response[3:].strip()
            files = json.loads(files_data) if files_data else []
            return jsonify({"files": files})
        else:
            return jsonify({"error": "Error al listar archivos: " + response}), 400
    except Exception as e:
        logging.error(f"Error al listar archivos: {e}")
        return jsonify({"error": "Error de conexión al servidor"}), 500

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a file to the server"""
    if 'file' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    try:
        # Get socket connection
        sock = get_socket_connection()

        # Read file data
        file_data = file.read()
        file_size = len(file_data)

        # Send upload command
        command = f"UPLOAD {file.filename} {file_size}"
        sock.send(command.encode())

        # Wait for server ready signal
        response = sock.recv(1024).decode()
        if not response.startswith("READY"):
            return jsonify({"error": "El servidor no está listo para recibir el archivo"}), 500

        # Send file data
        sock.sendall(file_data)

        # Get upload confirmation
        response = sock.recv(1024).decode()
        if response.startswith("OK"):
            return jsonify({"message": "Archivo subido exitosamente"})
        else:
            return jsonify({"error": "Error al subir archivo: " + response}), 400
    except Exception as e:
        logging.error(f"Error al subir archivo: {e}")
        return jsonify({"error": "Error de conexión al servidor"}), 500

@app.route('/api/files/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    """Download a file from the server"""
    try:
        # Get socket connection
        sock = get_socket_connection()

        # Send download command
        command = f"DOWNLOAD {filename}"
        sock.send(command.encode())

        # Receive initial response
        response = sock.recv(1024).decode()

        if not response.startswith("OK"):
            return jsonify({"error": "Error al descargar archivo: " + response}), 400

        # Parse file size
        parts = response.split()
        if len(parts) < 2:
            return jsonify({"error": "Respuesta del servidor inválida"}), 500

        file_size = int(parts[1])

        # Receive file data
        file_data = b""
        bytes_received = 0

        while bytes_received < file_size:
            chunk = sock.recv(min(4096, file_size - bytes_received))
            if not chunk:
                break
            file_data += chunk
            bytes_received += len(chunk)

        # Create temporary file
        temp_path = os.path.join('/tmp', filename)
        with open(temp_path, 'wb') as f:
            f.write(file_data)

        # Send file to client
        return send_file(temp_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logging.error(f"Error al descargar archivo: {e}")
        return jsonify({"error": "Error de conexión al servidor"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.pop('usuario', None)
    return jsonify({"message": "Sesión cerrada"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
