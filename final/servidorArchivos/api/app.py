import os
import sys
import ssl
import socket
import json
import logging
from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

# Importaciones de módulos propios
from cli.cliente.seguridad_ssl import establecer_conexion_ssl
from utils.config import verificar_configuracion_env

# Verificar configuración del archivo .env
verificar_configuracion_env()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuración de Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave para las sesiones
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos

# Habilitar CORS para el frontend
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

# Configuración de conexión al servidor
SERVIDOR_HOST = os.getenv("SERVIDOR_HOST", "127.0.0.1")
SERVIDOR_PORT = int(os.getenv("SERVIDOR_PORT", 1608))
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_uploads")

# Crear directorio de uploads si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Función para establecer conexión con el servidor de sockets
def conectar_servidor():
    try:
        conexion_ssl = establecer_conexion_ssl(SERVIDOR_HOST, SERVIDOR_PORT, verificar_cert=True)
        if not conexion_ssl:
            raise Exception("No se pudo establecer conexión con el servidor")
        return conexion_ssl
    except Exception as e:
        logging.error(f"Error al conectar con el servidor: {e}")
        raise

# Función para enviar comando al servidor y recibir respuesta
def enviar_comando(comando, conexion=None):
    conexion_propia = conexion is None
    
    try:
        if conexion_propia:
            conexion = conectar_servidor()
            
            # Autenticar si hay sesión activa
            if 'usuario' in session and 'password' in session:
                # Descartar mensaje de bienvenida
                conexion.recv(1024)
                
                # Enviar usuario
                conexion.recv(1024)  # Descartar prompt
                conexion.sendall(session['usuario'].encode('utf-8'))
                
                # Enviar contraseña
                conexion.recv(1024)  # Descartar prompt
                conexion.sendall(session['password'].encode('utf-8'))
                
                # Verificar autenticación
                respuesta_auth = conexion.recv(1024).decode('utf-8')
                if "✅ Autenticación exitosa" not in respuesta_auth:
                    raise Exception("Error de autenticación")
                
                # Descartar prompt de comando
                conexion.recv(1024)
            else:
                # Si no hay sesión, solo descartar el mensaje de bienvenida
                conexion.recv(1024)
        
        # Enviar comando
        conexion.sendall(comando.encode('utf-8'))
        
        # Recibir respuesta (descartar prompt si es necesario)
        if comando.upper() != "SALIR":
            respuesta = conexion.recv(1024).decode('utf-8')
            return respuesta
        
        return "Comando enviado"
    except Exception as e:
        logging.error(f"Error al enviar comando: {e}")
        raise
    finally:
        if conexion_propia and conexion:
            # Enviar SALIR para cerrar la conexión limpiamente
            try:
                conexion.sendall("SALIR".encode('utf-8'))
                conexion.recv(1024)  # Descartar respuesta
            except:
                pass
            conexion.close()

# Rutas de la API

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'usuario' in session:
        return jsonify({
            'authenticated': True,
            'usuario': session['usuario']
        })
    return jsonify({'authenticated': False})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400
    
    try:
        conexion = conectar_servidor()
        
        # Descartar mensaje de bienvenida
        conexion.recv(1024)
        
        # Enviar usuario
        conexion.recv(1024)  # Descartar prompt
        conexion.sendall(username.encode('utf-8'))
        
        # Enviar contraseña
        conexion.recv(1024)  # Descartar prompt
        conexion.sendall(password.encode('utf-8'))
        
        # Verificar autenticación
        respuesta_auth = conexion.recv(1024).decode('utf-8')
        
        if "✅ Autenticación exitosa" in respuesta_auth:
            # Guardar en sesión
            session['usuario'] = username
            session['password'] = password  # Necesario para reautenticar en cada comando
            
            # Cerrar conexión limpiamente
            conexion.recv(1024)  # Descartar prompt de comando
            conexion.sendall("SALIR".encode('utf-8'))
            conexion.close()
            
            return jsonify({'success': True, 'usuario': username})
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        logging.error(f"Error en login: {e}")
        return jsonify({'error': 'Error al conectar con el servidor'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400
    
    try:
        comando = f"REGISTRAR {username} {password}"
        respuesta = enviar_comando(comando)
        
        if "✅" in respuesta:
            return jsonify({'success': True, 'message': 'Usuario registrado correctamente'})
        else:
            return jsonify({'error': respuesta}), 400
    except Exception as e:
        logging.error(f"Error en registro: {e}")
        return jsonify({'error': 'Error al conectar con el servidor'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/files', methods=['GET'])
def list_files():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        respuesta = enviar_comando("LISTAR")
        
        # Parsear la respuesta para extraer los archivos
        files = []
        for line in respuesta.strip().split('\n'):
            if line and not line.startswith('📄'):
                parts = line.strip().split()
                if len(parts) >= 4:
                    name = parts[0]
                    size = int(parts[1])
                    date = ' '.join(parts[2:4])
                    
                    files.append({
                        'name': name,
                        'size': size,
                        'modified': date,
                        'type': 'file'
                    })
        
        return jsonify({'files': files})
    except Exception as e:
        logging.error(f"Error al listar archivos: {e}")
        return jsonify({'error': 'Error al obtener archivos'}), 500

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Guardar archivo temporalmente
        file.save(filepath)
        
        # Enviar comando de subida
        comando = f"SUBIR {filename}"
        
        # Establecer conexión
        conexion = conectar_servidor()
        
        # Autenticar
        conexion.recv(1024)  # Descartar mensaje de bienvenida
        conexion.recv(1024)  # Descartar prompt de usuario
        conexion.sendall(session['usuario'].encode('utf-8'))
        conexion.recv(1024)  # Descartar prompt de contraseña
        conexion.sendall(session['password'].encode('utf-8'))
        respuesta_auth = conexion.recv(1024).decode('utf-8')
        
        if "✅ Autenticación exitosa" not in respuesta_auth:
            return jsonify({'error': 'Error de autenticación'}), 401
        
        # Descartar prompt de comando
        conexion.recv(1024)
        
        # Enviar comando de subida
        conexion.sendall(comando.encode('utf-8'))
        
        # Leer respuesta inicial (confirmación para enviar archivo)
        respuesta = conexion.recv(1024).decode('utf-8')
        
        if "Listo para recibir" in respuesta:
            # Enviar archivo
            with open(filepath, 'rb') as f:
                data = f.read()
                conexion.sendall(data)
            
            # Leer respuesta final
            respuesta_final = conexion.recv(1024).decode('utf-8')
            
            # Cerrar conexión
            conexion.sendall("SALIR".encode('utf-8'))
            conexion.close()
            
            # Eliminar archivo temporal
            os.remove(filepath)
            
            if "✅" in respuesta_final:
                return jsonify({'success': True, 'message': 'Archivo subido correctamente'})
            else:
                return jsonify({'error': respuesta_final}), 500
        else:
            return jsonify({'error': respuesta}), 500
    except Exception as e:
        logging.error(f"Error al subir archivo: {e}")
        # Asegurarse de eliminar el archivo temporal si existe
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Error al subir archivo: {str(e)}'}), 500

@app.route('/api/files/download/<filename>', methods=['GET'])
def download_file(filename):
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    filename = secure_filename(filename)
    download_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Establecer conexión
        conexion = conectar_servidor()
        
        # Autenticar
        conexion.recv(1024)  # Descartar mensaje de bienvenida
        conexion.recv(1024)  # Descartar prompt de usuario
        conexion.sendall(session['usuario'].encode('utf-8'))
        conexion.recv(1024)  # Descartar prompt de contraseña
        conexion.sendall(session['password'].encode('utf-8'))
        respuesta_auth = conexion.recv(1024).decode('utf-8')
        
        if "✅ Autenticación exitosa" not in respuesta_auth:
            return jsonify({'error': 'Error de autenticación'}), 401
        
        # Descartar prompt de comando
        conexion.recv(1024)
        
        # Enviar comando de descarga
        comando = f"DESCARGAR {filename}"
        conexion.sendall(comando.encode('utf-8'))
        
        # Leer respuesta inicial
        respuesta = conexion.recv(1024).decode('utf-8')
        
        if "Enviando archivo" in respuesta:
            # Recibir y guardar archivo
            with open(download_path, 'wb') as f:
                while True:
                    data = conexion.recv(8192)
                    if not data:
                        break
                    f.write(data)
            
            # Cerrar conexión
            conexion.close()
            
            # Enviar archivo al cliente y luego eliminarlo
            response = send_file(download_path, as_attachment=True, download_name=filename)
            
            # Eliminar archivo después de enviarlo
            @response.call_on_close
            def on_close():
                if os.path.exists(download_path):
                    os.remove(download_path)
            
            return response
        else:
            return jsonify({'error': respuesta}), 500
    except Exception as e:
        logging.error(f"Error al descargar archivo: {e}")
        # Asegurarse de eliminar el archivo temporal si existe
        if os.path.exists(download_path):
            os.remove(download_path)
        return jsonify({'error': f'Error al descargar archivo: {str(e)}'}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    filename = secure_filename(filename)
    
    try:
        comando = f"ELIMINAR {filename}"
        respuesta = enviar_comando(comando)
        
        if "✅" in respuesta:
            return jsonify({'success': True, 'message': 'Archivo eliminado correctamente'})
        else:
            return jsonify({'error': respuesta}), 500
    except Exception as e:
        logging.error(f"Error al eliminar archivo: {e}")
        return jsonify({'error': f'Error al eliminar archivo: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)