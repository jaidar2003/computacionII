import socket
import ssl
import os

def create_ssl_connection(host, port):
    """Crea una conexión SSL con el servidor"""
    # Crear socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Configurar contexto SSL
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # No verificar certificado (solo para desarrollo)
    
    try:
        # Conectar al servidor
        sock.connect((host, port))
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        return ssl_sock
    except Exception as e:
        print(f"❌ Error al conectar con el servidor: {str(e)}")
        return None

def send_command(connection, command):
    """Envía un comando al servidor y recibe la respuesta"""
    try:
        # Enviar comando
        connection.sendall(command.encode('utf-8'))
        
        # Recibir respuesta
        response = b""
        chunk = connection.recv(4096)
        while chunk:
            response += chunk
            # Verificar si hay más datos para recibir
            try:
                connection.settimeout(0.5)  # Esperar 0.5 segundos por más datos
                chunk = connection.recv(4096)
            except socket.timeout:
                break
        
        connection.settimeout(None)  # Restaurar timeout
        return response.decode('utf-8').strip()
    except Exception as e:
        print(f"❌ Error en la comunicación con el servidor: {str(e)}")
        return None

def receive_prompt(connection):
    """Recibe un prompt del servidor"""
    try:
        return connection.recv(1024).decode('utf-8').strip()
    except Exception as e:
        print(f"❌ Error al recibir prompt: {str(e)}")
        return None

def send_response(connection, response):
    """Envía una respuesta a un prompt del servidor"""
    try:
        connection.sendall(response.encode('utf-8'))
        return True
    except Exception as e:
        print(f"❌ Error al enviar respuesta: {str(e)}")
        return False

def upload_file(connection, file_path):
    """Sube un archivo al servidor"""
    try:
        # Obtener nombre del archivo
        filename = os.path.basename(file_path)
        
        # Leer archivo
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Enviar comando SUBIR con el nombre del archivo
        command = f"SUBIR {filename}"
        connection.sendall(command.encode('utf-8'))
        
        # Recibir respuesta inicial (si el servidor está listo para recibir)
        initial_response = connection.recv(1024).decode('utf-8').strip()
        if "listo para recibir" not in initial_response.lower():
            return initial_response
        
        # Enviar datos del archivo
        connection.sendall(file_data)
        
        # Recibir respuesta final
        response = connection.recv(4096).decode('utf-8').strip()
        return response
    except Exception as e:
        print(f"❌ Error al subir archivo: {str(e)}")
        return None

def download_file(connection, filename):
    """Descarga un archivo del servidor"""
    try:
        # Enviar comando DESCARGAR con el nombre del archivo
        command = f"DESCARGAR {filename}"
        connection.sendall(command.encode('utf-8'))
        
        # Recibir datos del archivo
        file_data = b''
        chunk = connection.recv(4096)
        
        # Si el primer chunk contiene un mensaje de error, retornarlo
        if chunk.startswith(b'\xe2\x9d\x8c'):  # Emoji ❌
            return chunk.decode('utf-8').strip()
        
        # Si no es un error, seguir recibiendo datos
        while chunk:
            file_data += chunk
            try:
                connection.settimeout(0.5)  # Esperar 0.5 segundos por más datos
                chunk = connection.recv(4096)
            except socket.timeout:
                break
        
        connection.settimeout(None)  # Restaurar timeout
        
        # Guardar archivo
        with open(filename, 'wb') as f:
            f.write(file_data)
            
        return f"✅ Archivo {filename} descargado correctamente"
    except Exception as e:
        print(f"❌ Error al descargar archivo: {str(e)}")
        return None