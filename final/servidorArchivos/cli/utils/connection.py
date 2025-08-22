import socket
import ssl
import os

def create_ssl_connection(host, port):
    """Crea una conexión SSL con el servidor"""
    # Determinar si la dirección es IPv6
    is_ipv6 = ':' in host
    
    # Configurar contexto SSL
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # No verificar certificado (solo para desarrollo)
    
    try:
        # Manejar direcciones IPv6 link-local con identificador de zona
        if is_ipv6 and '%' in host:
            # Crear socket IPv6
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            
            # Separar la dirección IPv6 del identificador de zona y el puerto
            if ':' in host.split('%')[1]:  # Si hay un puerto después del identificador de zona
                addr_parts = host.split('%')
                ipv6_addr = addr_parts[0]
                zone_port_parts = addr_parts[1].split(':')
                zone_id = zone_port_parts[0]
                # El puerto ya viene como parámetro, no necesitamos extraerlo
            else:
                ipv6_addr = host.split('%')[0]
                zone_id = host.split('%')[1]
            
            try:
                # Obtener el índice de la interfaz a partir del identificador de zona
                if_idx = socket.if_nametoindex(zone_id)
                # Conectar usando la dirección IPv6, puerto, flow info y scope id
                sock.connect((ipv6_addr, port, 0, if_idx))
            except (socket.error, OSError) as e:
                print(f"❌ Error al conectar con IPv6 link-local: {str(e)}")
                print("ℹ️ Intentando conexión alternativa...")
                # Intentar una conexión alternativa sin el índice de interfaz
                try:
                    sock.connect((host, port))
                except Exception as e2:
                    print(f"❌ Error en conexión alternativa: {str(e2)}")
                    return None
        else:
            # Crear socket con el tipo adecuado para direcciones normales
            if is_ipv6:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Conectar al servidor
            sock.connect((host, port))
        
        # Envolver la conexión con SSL
        ssl_sock = context.wrap_socket(sock, server_hostname=host.split('%')[0] if '%' in host else host)
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