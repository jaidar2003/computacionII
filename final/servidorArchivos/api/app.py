import os
import sys
import ssl
import socket
import json
import logging
import select
from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

# Importaciones de módulos propios
from utils.ssl_utils import establecer_conexion_ssl
from utils.config import verificar_configuracion_env

# Verificar configuración del archivo .env
verificar_configuracion_env()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuración de Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave para las sesiones
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True  # Cambiar a True para mantener la sesión
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos
app.config['SESSION_COOKIE_SECURE'] = False  # Cambiar a True en producción con HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Usar 'None' en producción con HTTPS

# Habilitar CORS para el frontend
# En producción, reemplazar "*" con la URL específica del frontend
CORS(app, supports_credentials=True, origins=["*"], allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Disposition"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

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
        print(f"Intentando conectar al servidor en {SERVIDOR_HOST}:{SERVIDOR_PORT}...")
        conexion_ssl = establecer_conexion_ssl(SERVIDOR_HOST, SERVIDOR_PORT, verificar_cert=True)
        if not conexion_ssl:
            error_msg = "No se pudo establecer conexión con el servidor"
            print(error_msg)
            raise Exception(error_msg)
        print("Conexión establecida con éxito")
        return conexion_ssl
    except Exception as e:
        error_msg = f"Error al conectar con el servidor: {e}"
        logging.error(error_msg)
        print(error_msg)
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
            # Aumentar el tamaño del buffer y manejar respuestas grandes
            buffer_size = 32768  # 32KB buffer
            respuesta_completa = ""
            while True:
                parte = conexion.recv(buffer_size).decode('utf-8')
                respuesta_completa += parte
                
                # Si la respuesta es más pequeña que el buffer, hemos terminado
                if len(parte) < buffer_size:
                    break
                
                # Verificar si hay más datos disponibles
                # (Opcional: puedes agregar un pequeño timeout aquí)
                conexion.settimeout(0.5)
                try:
                    if not select.select([conexion], [], [], 0.1)[0]:
                        break
                except:
                    break
                finally:
                    # Restaurar timeout normal
                    conexion.settimeout(None)

            return respuesta_completa

        return "Comando enviado"
    except Exception as e:
        error_msg = f"Error al enviar comando '{comando}': {e}"
        logging.error(error_msg)
        print(error_msg)
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
    # Log para debugging de sesiones
    logging.debug(f"Verificando autenticación. Sesión actual: {dict(session)}")

    if 'usuario' in session:
        logging.info(f"Usuario autenticado: {session['usuario']}")
        return jsonify({
            'authenticated': True,
            'usuario': session['usuario'],
            'permisos': session.get('permisos', 'lectura')  # Include permissions in the response
        })

    logging.info("Usuario no autenticado")
    return jsonify({'authenticated': False})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400

    try:
        # Primero autenticar con la base de datos para obtener los permisos
        from baseDeDatos.db import autenticar_usuario
        auth_result = autenticar_usuario(username, password)

        if not auth_result:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        user_id, permisos = auth_result

        # Luego autenticar con el servidor de sockets
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
            session['permisos'] = permisos  # Guardar permisos en la sesión

            # Cerrar conexión limpiamente
            conexion.recv(1024)  # Descartar prompt de comando
            conexion.sendall("SALIR".encode('utf-8'))
            conexion.close()

            return jsonify({
                'success': True, 
                'usuario': username,
                'permisos': permisos
            })
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        logging.error(f"Error en login: {e}")
        print(f"Error en login: {e}")
        return jsonify({'error': f'Error al conectar con el servidor: {str(e)}'}), 500

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
        logging.warning(f"Intento de listar archivos sin sesión activa")
        return jsonify({'error': 'No autenticado'}), 401

    try:
        logging.info(f"Listando archivos para usuario: {session.get('usuario')}")
        respuesta = enviar_comando("LISTAR")

        # Log de la respuesta para debugging
        logging.debug(f"Respuesta del servidor para LISTAR: {respuesta}")
        print(f"Respuesta LISTAR: {respuesta}")

        # Parsear la respuesta para extraer los archivos
        files = []
        if not respuesta or respuesta.strip() == "":
            logging.warning("Respuesta vacía del servidor al listar archivos")
            return jsonify({'files': [], 'warning': 'No se encontraron archivos'})

        for line in respuesta.strip().split('\n'):
            if line:
                try:
                    # Si la línea comienza con el emoji, quitar el emoji
                    if line.startswith('📄 '):
                        line = line[2:].strip()

                    parts = line.strip().split()
                    if len(parts) >= 1:  # Al menos debe tener un nombre de archivo
                        name = parts[0]
                        # Valores predeterminados en caso de que no haya información completa
                        size = int(parts[1]) if len(parts) > 1 else 0
                        date = ' '.join(parts[2:4]) if len(parts) > 3 else ''

                        files.append({
                            'name': name,
                            'size': size,
                            'modified': date,
                            'type': 'file'
                        })
                except Exception as parse_error:
                    logging.error(f"Error al parsear línea '{line}': {parse_error}")
                    continue

        logging.info(f"Se encontraron {len(files)} archivos")
        return jsonify({'files': files})
    except Exception as e:
        logging.error(f"Error al listar archivos: {e}")
        print(f"Error al listar archivos: {e}")
        return jsonify({'error': f'Error al obtener archivos: {str(e)}'}), 500

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

    conexion = None
    try:
        # Guardar archivo temporalmente
        file.save(filepath)
        logging.info(f"Archivo guardado temporalmente en {filepath}")

        # Calcular hash SHA-256
        import hashlib
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            logging.info(f"Hash calculado para {filename}: {file_hash}")

        # Obtener tamaño del archivo
        file_size = os.path.getsize(filepath)
        logging.info(f"Tamaño del archivo {filename}: {file_size} bytes")

        # Verificar que el archivo no sea demasiado grande
        max_size = 100 * 1024 * 1024  # 100 MB
        if file_size > max_size:
            return jsonify({'error': f'El archivo es demasiado grande. Tamaño máximo: {max_size/1024/1024} MB'}), 413

        # Enviar comando de subida con hash
        comando = f"SUBIR {filename} {file_hash}"
        logging.info(f"Comando de subida: {comando}")

        # Establecer conexión con timeout aumentado
        try:
            conexion = conectar_servidor()
            # Configurar timeout más largo para archivos grandes
            conexion.settimeout(300)  # 5 minutos
        except Exception as e:
            logging.error(f"Error al conectar con el servidor: {e}")
            return jsonify({'error': f'Error al conectar con el servidor: {str(e)}'}), 500

        try:
            # Autenticar
            conexion.recv(1024)  # Descartar mensaje de bienvenida
            conexion.recv(1024)  # Descartar prompt de usuario
            conexion.sendall(session['usuario'].encode('utf-8'))
            conexion.recv(1024)  # Descartar prompt de contraseña
            conexion.sendall(session['password'].encode('utf-8'))
            respuesta_auth = conexion.recv(1024).decode('utf-8')

            if "✅ Autenticación exitosa" not in respuesta_auth:
                logging.error(f"Error de autenticación: {respuesta_auth}")
                return jsonify({'error': 'Error de autenticación'}), 401

            # Descartar prompt de comando
            conexion.recv(1024)

            # Enviar comando de subida
            conexion.sendall(comando.encode('utf-8'))
            logging.info(f"Comando enviado: {comando}")

            # Leer respuesta inicial (confirmación para enviar archivo)
            respuesta = conexion.recv(1024).decode('utf-8')
            logging.info(f"Respuesta del servidor: {respuesta}")
        except socket.timeout as e:
            logging.error(f"Timeout durante la autenticación o envío de comando: {e}")
            return jsonify({'error': f'Tiempo de espera agotado durante la comunicación con el servidor: {str(e)}'}), 504
        except Exception as e:
            logging.error(f"Error durante la autenticación o envío de comando: {e}")
            return jsonify({'error': f'Error durante la comunicación con el servidor: {str(e)}'}), 500

        if "Listo para recibir" in respuesta:
            try:
                # Enviar archivo
                with open(filepath, 'rb') as f:
                    # Obtener tamaño del archivo
                    f.seek(0, os.SEEK_END)
                    tamaño = f.tell()
                    f.seek(0)  # Volver al inicio del archivo
                    
                    logging.info(f"Iniciando transferencia de archivo {filename} ({tamaño} bytes)")
                    
                    # Enviar primero el tamaño del archivo
                    conexion.sendall(str(tamaño).encode('utf-8') + b'\n')
                    
                    # Enviar el archivo en chunks para evitar problemas de memoria
                    chunk_size = 8192  # 8KB chunks
                    bytes_enviados = 0
                    
                    try:
                        while bytes_enviados < tamaño:
                            chunk = f.read(min(chunk_size, tamaño - bytes_enviados))
                            if not chunk:
                                break
                            conexion.sendall(chunk)
                            bytes_enviados += len(chunk)
                            
                            # Registrar progreso cada 1MB
                            if bytes_enviados % (1024 * 1024) == 0:
                                logging.info(f"Progreso: {bytes_enviados}/{tamaño} bytes ({bytes_enviados/tamaño*100:.1f}%)")
                        
                        logging.info(f"Transferencia completada: {bytes_enviados}/{tamaño} bytes para {filename}")
                    except socket.timeout as e:
                        logging.error(f"Timeout durante la transferencia del archivo: {e}")
                        return jsonify({'error': f'Tiempo de espera agotado durante la transferencia del archivo. Intente con un archivo más pequeño o cuando la red esté menos congestionada.'}), 504
                    except ConnectionError as e:
                        logging.error(f"Error de conexión durante la transferencia: {e}")
                        return jsonify({'error': f'La conexión se cerró durante la transferencia del archivo: {str(e)}'}), 500
                
                # Leer respuesta final
                try:
                    respuesta_final = conexion.recv(1024).decode('utf-8')
                    logging.info(f"Respuesta final del servidor: {respuesta_final}")
                except socket.timeout:
                    logging.warning("Timeout al esperar respuesta final, pero el archivo podría haberse subido correctamente")
                    return jsonify({'warning': 'No se recibió confirmación del servidor, pero el archivo podría haberse subido correctamente. Verifique en la lista de archivos.'}), 202
                
                if "✅" in respuesta_final:
                    return jsonify({'success': True, 'message': 'Archivo subido correctamente'})
                else:
                    logging.error(f"Error en respuesta final: {respuesta_final}")
                    return jsonify({'error': respuesta_final}), 500
            except Exception as e:
                logging.error(f"Error durante la transferencia del archivo: {e}")
                return jsonify({'error': f'Error durante la transferencia del archivo: {str(e)}'}), 500
        else:
            logging.error(f"El servidor no está listo para recibir: {respuesta}")
            return jsonify({'error': respuesta}), 500
    except Exception as e:
        logging.error(f"Error al subir archivo: {e}")
        return jsonify({'error': f'Error al subir archivo: {str(e)}'}), 500
    finally:
        # Limpiar recursos
        if conexion:
            try:
                conexion.sendall("SALIR".encode('utf-8'))
                conexion.close()
                logging.info("Conexión cerrada correctamente")
            except:
                logging.warning("No se pudo cerrar la conexión limpiamente")
        
        # Eliminar archivo temporal
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logging.info(f"Archivo temporal eliminado: {filepath}")
            except Exception as e:
                logging.warning(f"No se pudo eliminar el archivo temporal {filepath}: {e}")

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

        if "Listo para enviar" in respuesta:
            # Enviar confirmación "LISTO" al servidor
            conexion.sendall("LISTO".encode('utf-8'))
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

@app.route('/api/files/rename', methods=['PUT'])
def rename_file():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.json
    old_name = secure_filename(data.get('oldName', ''))
    new_name = secure_filename(data.get('newName', ''))

    if not old_name or not new_name:
        return jsonify({'error': 'Nombres de archivo inválidos'}), 400

    try:
        comando = f"RENOMBRAR {old_name} {new_name}"
        respuesta = enviar_comando(comando)

        if "✅" in respuesta or "✏️" in respuesta:
            return jsonify({'success': True, 'message': f'Archivo renombrado de {old_name} a {new_name}'})
        else:
            return jsonify({'error': respuesta}), 500
    except Exception as e:
        logging.error(f"Error al renombrar archivo: {e}")
        return jsonify({'error': f'Error al renombrar archivo: {str(e)}'}), 500

@app.route('/api/files/verify/<filename>', methods=['GET'])
def verify_file(filename):
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Verificar que el usuario tenga permisos de lectura
    if session.get('permisos') not in ['lectura', 'escritura', 'admin']:
        return jsonify({'error': 'No tienes permisos suficientes para verificar archivos'}), 403

    filename = secure_filename(filename)

    try:
        comando = f"VERIFICAR {filename}"
        respuesta = enviar_comando(comando)

        # Extraer información relevante de la respuesta
        estado = "desconocido"
        detalles = ""
        
        # Verificar si hay información de verificación
        if "No hay información de verificación" in respuesta:
            estado = "sin_info"
            detalles = "No se encontró información de verificación para este archivo. Intente subir el archivo nuevamente."
        # Verificar estado basado en el contenido de la respuesta
        elif "OK -" in respuesta or "ok" in respuesta.lower():
            estado = "ok"
            detalles = "El archivo ha sido verificado y está en buen estado."
        elif "CORRUPTO" in respuesta:
            estado = "corrupto"
            detalles = "El archivo está corrupto o ha sido modificado."
        elif "INFECTADO" in respuesta:
            estado = "infectado"
            detalles = "El archivo podría contener malware."
        
        # Extraer información adicional si está disponible
        info_integridad = None
        info_virus = None
        
        if "Integridad: " in respuesta:
            try:
                info_integridad = respuesta.split("Integridad: ")[1].split(" -")[0].strip()
            except:
                pass
                
        if "Antivirus: " in respuesta:
            try:
                info_virus = respuesta.split("Antivirus: ")[1].split(" -")[0].strip()
            except:
                pass
        
        # Obtener el hash del archivo .hash si existe
        hash_value = None
        hash_file_path = os.path.join(os.getenv("SERVIDOR_DIR"), f"{filename}.hash")
        
        # Verificar si existe el archivo de hash en el servidor
        try:
            # Enviar comando para verificar si existe el archivo hash
            hash_check = enviar_comando(f"LISTAR {filename}.hash")
            logging.info(f"Resultado de verificación de existencia del hash: {hash_check}")
            
            if "No hay archivos" not in hash_check and "no encontrado" not in hash_check:
                # El archivo hash existe, obtener su contenido
                hash_response = enviar_comando(f"DESCARGAR {filename}.hash")
                logging.info(f"Respuesta completa al descargar hash: {hash_response}")
                
                # Limpiar el hash (eliminar mensajes adicionales)
                if hash_response:
                    # Método 1: Extraer después del checkmark
                    if "✅" in hash_response:
                        hash_value = hash_response.split("✅")[1].strip()
                        logging.info(f"Hash después de split por ✅: {hash_value}")
                        
                        # Limpiar cualquier texto adicional después del hash
                        if "enviado correctamente" in hash_value:
                            hash_value = hash_value.split("enviado correctamente")[0].strip()
                        
                        # Eliminar cualquier texto que no sea parte del hash (64 caracteres hexadecimales)
                        import re
                        hash_match = re.search(r'[0-9a-f]{64}', hash_value)
                        if hash_match:
                            hash_value = hash_match.group(0)
                    
                    # Método 2: Si el método 1 falló, intentar extraer directamente el patrón de hash
                    if not hash_value or len(hash_value) != 64:
                        import re
                        hash_match = re.search(r'[0-9a-f]{64}', hash_response)
                        if hash_match:
                            hash_value = hash_match.group(0)
                
                logging.info(f"Hash final extraído: {hash_value}")
        except Exception as e:
            logging.warning(f"No se pudo obtener el hash para {filename}: {e}")

        return jsonify({
            'success': True, 
            'filename': filename,
            'status': estado,
            'details': detalles,
            'integrity': info_integridad,
            'antivirus': info_virus,
            'hash': hash_value,  # Añadir el hash a la respuesta
            'message': respuesta
        })
    except Exception as e:
        logging.error(f"Error al verificar archivo: {e}")
        return jsonify({'error': f'Error al verificar archivo: {str(e)}'}), 500

# Endpoint para solicitar cambio de permisos
@app.route('/api/permissions/request', methods=['POST'])
def request_permissions():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    data = request.json
    permission_type = data.get('permissionType')
    
    if not permission_type:
        return jsonify({'error': 'Tipo de permiso requerido'}), 400
    
    try:
        comando = f"SOLICITAR_PERMISOS {permission_type}"
        respuesta = enviar_comando(comando)
        
        if "✅" in respuesta:
            return jsonify({'success': True, 'message': respuesta})
        else:
            return jsonify({'error': respuesta}), 400
    except Exception as e:
        logging.error(f"Error al solicitar permisos: {e}")
        return jsonify({'error': f'Error al solicitar permisos: {str(e)}'}), 500

# Endpoint para ver solicitudes de permisos
@app.route('/api/permissions/requests', methods=['GET'])
def view_permission_requests():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    try:
        comando = "VER_SOLICITUDES"
        respuesta = enviar_comando(comando)
        
        # Parsear la respuesta para extraer las solicitudes
        requests = []
        if "No hay solicitudes" not in respuesta:
            for line in respuesta.strip().split('\n'):
                if "ID:" in line:
                    try:
                        # Extraer información de la línea
                        request_info = {}
                        
                        # Extraer ID
                        id_part = line.split('ID:')[1].split('|')[0].strip()
                        request_info['id'] = id_part
                        
                        # Extraer usuario si es admin
                        if "Usuario:" in line:
                            user_part = line.split('Usuario:')[1].split('|')[0].strip()
                            request_info['username'] = user_part
                        
                        # Extraer permiso
                        if "Permiso:" in line:
                            perm_part = line.split('Permiso:')[1].split('|')[0].strip()
                            request_info['permission'] = perm_part
                        
                        # Extraer estado si no es admin
                        if "Estado:" in line:
                            state_part = line.split('Estado:')[1].split('|')[0].strip()
                            request_info['status'] = state_part
                        
                        # Extraer fecha
                        if "Fecha:" in line:
                            date_part = line.split('Fecha:')[1].strip()
                            request_info['date'] = date_part
                        
                        requests.append(request_info)
                    except Exception as parse_error:
                        logging.error(f"Error al parsear línea '{line}': {parse_error}")
                        continue
        
        return jsonify({'requests': requests, 'rawResponse': respuesta})
    except Exception as e:
        logging.error(f"Error al ver solicitudes: {e}")
        return jsonify({'error': f'Error al ver solicitudes: {str(e)}'}), 500

# Endpoint para aprobar/rechazar solicitudes de permisos (solo admin)
@app.route('/api/permissions/approve', methods=['POST'])
def approve_permission():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Verificar que el usuario sea administrador
    if session.get('permisos') != 'admin':
        return jsonify({'error': 'No tienes permisos de administrador'}), 403
    
    data = request.json
    request_id = data.get('requestId')
    decision = data.get('decision')  # 'aprobar' o 'rechazar'
    
    if not request_id or not decision:
        return jsonify({'error': 'ID de solicitud y decisión son requeridos'}), 400
    
    try:
        comando = f"APROBAR_PERMISOS {request_id} {decision}"
        respuesta = enviar_comando(comando)
        
        if "✅" in respuesta or "⛔" in respuesta:
            return jsonify({'success': True, 'message': respuesta})
        else:
            return jsonify({'error': respuesta}), 400
    except Exception as e:
        logging.error(f"Error al aprobar/rechazar solicitud: {e}")
        return jsonify({'error': f'Error al procesar solicitud: {str(e)}'}), 500

# Endpoint para listar usuarios (solo admin)
@app.route('/api/users', methods=['GET'])
def list_users():
    if 'usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    # Verificar que el usuario sea administrador
    if session.get('permisos') != 'admin':
        return jsonify({'error': 'No tienes permisos de administrador'}), 403
    
    try:
        comando = "LISTAR_USUARIOS"
        respuesta = enviar_comando(comando)
        
        # Parsear la respuesta para extraer los usuarios
        users = []
        if "No hay usuarios" not in respuesta:
            for line in respuesta.strip().split('\n'):
                if "ID:" in line:
                    try:
                        # Extraer información de la línea
                        user_info = {}
                        
                        # Extraer ID
                        id_part = line.split('ID:')[1].split('|')[0].strip()
                        user_info['id'] = id_part
                        
                        # Extraer nombre de usuario
                        if "Usuario:" in line:
                            user_part = line.split('Usuario:')[1].split('|')[0].strip()
                            user_info['username'] = user_part
                        
                        # Extraer permiso
                        if "Permiso:" in line:
                            perm_part = line.split('Permiso:')[1].strip()
                            user_info['permission'] = perm_part
                        
                        users.append(user_info)
                    except Exception as parse_error:
                        logging.error(f"Error al parsear línea '{line}': {parse_error}")
                        continue
        
        return jsonify({'users': users, 'rawResponse': respuesta})
    except Exception as e:
        logging.error(f"Error al listar usuarios: {e}")
        return jsonify({'error': f'Error al listar usuarios: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)
