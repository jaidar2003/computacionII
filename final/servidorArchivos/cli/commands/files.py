import os
import sys
import socket
from ..utils import config
from ..utils.session import load_session, check_auth
from ..utils.connection import create_ssl_connection, send_command, upload_file as conn_upload_file, download_file as conn_download_file, receive_prompt, send_response
from ..utils.visual import (
    print_success, print_error, print_info, print_warning, print_header,
    format_success, format_error, format_info, format_warning, 
    print_table_header, print_table_row, BOLD, RESET, SUCCESS, ERROR, WARNING, INFO
)
from tqdm import tqdm

def _authenticate_with_session(connection):
    """Autenticar con la sesión guardada"""
    session = load_session()
    if not session:
        raise Exception("No hay sesión activa")
    
    username = session.get("user", "Usuario")
    
    # Recibir mensaje de bienvenida (silenciosamente)
    welcome = receive_prompt(connection)
    
    # Recibir prompt de usuario (silenciosamente)
    user_prompt = receive_prompt(connection)
    
    # Enviar nombre de usuario
    print_info(f"Autenticando como {BOLD}{username}{RESET}...", end="\r")
    send_response(connection, session["user"])
    
    # Recibir prompt de contraseña (silenciosamente)
    pass_prompt = receive_prompt(connection)
    
    # Enviar contraseña (usar contraseña real de la sesión)
    send_response(connection, session.get("password", ""))
    
    # Recibir resultado de autenticación
    auth_result = receive_prompt(connection)
    
    # Si la autenticación falló, lanzar excepción
    if "❌" in auth_result:
        print_error(f"Error de autenticación para {BOLD}{username}{RESET}")
        raise Exception("Error de autenticación")
    
    # Limpiar la línea de "Autenticando..."
    sys.stdout.write("\033[K")
    
    return auth_result

@check_auth
def list_files(silent=False):
    """Listar archivos disponibles
    
    Args:
        silent (bool): Si es True, no muestra la salida en pantalla.
                      Útil para actualizar la lista de archivos en el modo interactivo.
    
    Returns:
        list: Lista de nombres de archivos si silent es True, None en caso contrario.
    """
    if not silent:
        print_info("Conectando al servidor...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        if not silent:
            print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return [] if silent else None
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        if not silent:
            print_info("Obteniendo lista de archivos...")
        
        # Enviar comando LISTAR
        response = send_command(connection, "LISTAR")
        
        # Cerrar conexión
        connection.close()
        
        # Lista para almacenar nombres de archivos (para modo silencioso)
        file_names = []
        
        # Procesar la respuesta para mostrarla de forma más amigable
        if "No hay archivos" in response:
            if not silent:
                print_warning("No hay archivos disponibles en el servidor.")
                print_info("Usa el comando 'upload' para subir archivos.")
            return file_names if silent else None
        
        # Extraer la lista de archivos de la respuesta
        # La respuesta tiene un formato como:
        # "✅ Archivos disponibles:\narchivo1.txt (1.23 KB) - 2023-01-01 12:00:00\narchivo2.txt (4.56 KB) - 2023-01-02 12:00:00"
        lines = response.split('\n')
        
        if not silent:
            # Mostrar encabezado
            print_header("ARCHIVOS DISPONIBLES")
            
            # Definir anchos de columna
            widths = [40, 15, 25]
            
            # Mostrar encabezado de tabla
            print_table_header(["Nombre", "Tamaño", "Modificado"], widths)
        
        # Procesar archivos
        for line in lines[1:]:  # Saltar la primera línea que es el encabezado
            if not line.strip():
                continue
                
            # Intentar extraer nombre, tamaño y fecha
            try:
                # Formato esperado: "archivo.txt (1.23 KB) - 2023-01-01 12:00:00"
                name_part = line.split(' (')[0].strip()
                size_part = line.split(' (')[1].split(')')[0].strip()
                date_part = line.split(' - ')[1].strip() if ' - ' in line else ""
                
                # Agregar nombre a la lista para modo silencioso
                file_names.append(name_part)
                
                if not silent:
                    print_table_row([name_part, size_part, date_part], widths)
            except IndexError:
                # Si no se puede parsear, mostrar la línea completa si no es silencioso
                if not silent:
                    print(line)
        
        # Retornar lista de nombres de archivos si es modo silencioso
        return file_names if silent else None
        
    except Exception as e:
        if not silent:
            print_error(f"Error al listar archivos: {str(e)}")
        if connection:
            connection.close()
        return [] if silent else None

@check_auth
def upload_file(file_path):
    """Subir un archivo al servidor"""
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        print_error(f"El archivo {BOLD}{file_path}{RESET} no existe")
        return
    
    # Obtener información del archivo
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    print_info(f"Conectando al servidor para subir {BOLD}{filename}{RESET} ({format_size(file_size)})...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        # Implementar nuestra propia función de subida con barra de progreso
        try:
            # Enviar comando SUBIR con el nombre del archivo
            command = f"SUBIR {filename}"
            connection.sendall(command.encode('utf-8'))
            
            # Recibir respuesta inicial (si el servidor está listo para recibir)
            initial_response = connection.recv(1024).decode('utf-8').strip()
            if "listo para recibir" not in initial_response.lower():
                print_error(f"Error al iniciar la subida: {initial_response}")
                connection.close()
                return
            
            # Leer y enviar el archivo con barra de progreso
            with open(file_path, 'rb') as f:
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Subiendo {filename}") as pbar:
                    # Leer y enviar en chunks para mostrar progreso
                    chunk_size = 8192
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        connection.sendall(chunk)
                        pbar.update(len(chunk))
            
            # Recibir respuesta final
            response = connection.recv(4096).decode('utf-8').strip()
            
            if "✅" in response:
                print_success(f"Archivo {BOLD}{filename}{RESET} subido correctamente")
            else:
                print_error(f"Error al subir archivo: {response}")
        
        except Exception as e:
            print_error(f"Error al subir archivo: {str(e)}")
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def download_file(filename):
    """Descargar un archivo del servidor"""
    print_info(f"Conectando al servidor para descargar {BOLD}{filename}{RESET}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        # Implementar nuestra propia función de descarga con barra de progreso
        try:
            # Enviar comando DESCARGAR con el nombre del archivo
            command = f"DESCARGAR {filename}"
            connection.sendall(command.encode('utf-8'))
            
            # Recibir los primeros bytes para verificar si hay error
            initial_chunk = connection.recv(4096)
            
            # Si el primer chunk contiene un mensaje de error, mostrarlo y salir
            if initial_chunk.startswith(b'\xe2\x9d\x8c'):  # Emoji ❌
                error_message = initial_chunk.decode('utf-8').strip()
                print_error(f"Error al descargar archivo: {error_message}")
                connection.close()
                return
            
            # Si no es un error, comenzar a guardar el archivo
            file_data = initial_chunk
            
            # Intentar determinar el tamaño del archivo para la barra de progreso
            # (esto es aproximado ya que no tenemos el tamaño exacto)
            content_length = len(initial_chunk)
            estimated_size = content_length * 10  # Estimación inicial
            
            # Crear barra de progreso
            with tqdm(total=estimated_size, unit='B', unit_scale=True, desc=f"Descargando {filename}") as pbar:
                # Actualizar con los bytes ya recibidos
                pbar.update(content_length)
                
                # Seguir recibiendo datos
                while True:
                    try:
                        connection.settimeout(0.5)  # Esperar 0.5 segundos por más datos
                        chunk = connection.recv(4096)
                        if not chunk:
                            break
                        
                        file_data += chunk
                        pbar.update(len(chunk))
                        
                        # Ajustar el tamaño estimado si es necesario
                        if pbar.n >= pbar.total * 0.8:
                            pbar.total = pbar.total * 1.5
                    except socket.timeout:
                        break
            
            connection.settimeout(None)  # Restaurar timeout
            
            # Guardar archivo
            with open(filename, 'wb') as f:
                f.write(file_data)
            
            print_success(f"Archivo {BOLD}{filename}{RESET} descargado correctamente ({format_size(len(file_data))})")
        
        except Exception as e:
            print_error(f"Error al descargar archivo: {str(e)}")
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def delete_file(filename):
    """Eliminar un archivo del servidor"""
    # Confirmar la eliminación con un mensaje coloreado
    print_warning(f"¿Estás seguro de que deseas eliminar {BOLD}{filename}{RESET}?")
    confirm = input(f"{WARNING}Esta acción no se puede deshacer (s/n): {RESET}")
    
    if confirm.lower() != 's':
        print_info("Operación cancelada")
        return
    
    print_info(f"Conectando al servidor para eliminar {BOLD}{filename}{RESET}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        print_info(f"Eliminando archivo {BOLD}{filename}{RESET}...")
        
        # Enviar comando ELIMINAR
        response = send_command(connection, f"ELIMINAR {filename}")
        
        if "✅" in response:
            print_success(f"Archivo {BOLD}{filename}{RESET} eliminado correctamente")
        else:
            print_error(f"Error al eliminar archivo: {response}")
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def rename_file(old_name, new_name):
    """Renombrar un archivo en el servidor"""
    print_info(f"Conectando al servidor para renombrar {BOLD}{old_name}{RESET} a {BOLD}{new_name}{RESET}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        print_info(f"Renombrando archivo {BOLD}{old_name}{RESET} a {BOLD}{new_name}{RESET}...")
        
        # Enviar comando RENOMBRAR
        response = send_command(connection, f"RENOMBRAR {old_name} {new_name}")
        
        if "✅" in response:
            print_success(f"Archivo renombrado correctamente de {BOLD}{old_name}{RESET} a {BOLD}{new_name}{RESET}")
        else:
            print_error(f"Error al renombrar archivo: {response}")
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def verify_file(filename=None):
    """Verificar la integridad de un archivo o todos los archivos"""
    if filename:
        print_info(f"Conectando al servidor para verificar el archivo {BOLD}{filename}{RESET}...")
    else:
        print_info("Conectando al servidor para verificar todos los archivos...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        # Enviar comando VERIFICAR
        command = "VERIFICAR"
        if filename:
            command = f"VERIFICAR {filename}"
            print_info(f"Verificando archivo {BOLD}{filename}{RESET}...")
        else:
            print_info("Verificando todos los archivos...")
            print_warning("Esta operación puede tardar varios minutos para muchos archivos.")
        
        response = send_command(connection, command)
        
        # Cerrar conexión
        connection.close()
        
        # Procesar la respuesta para mostrarla de forma más amigable
        if "✅" in response:
            # Mostrar encabezado
            print_header("RESULTADO DE LA VERIFICACIÓN")
            
            # Extraer información de la respuesta
            lines = response.split('\n')
            
            # Procesar cada línea
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Colorear según el tipo de información
                if "Hash" in line or "SHA-256" in line:
                    # Resaltar el hash
                    parts = line.split(": ", 1)
                    if len(parts) == 2:
                        print(f"{INFO}{parts[0]}: {BOLD}{parts[1]}{RESET}")
                    else:
                        print(line)
                elif "Integridad" in line:
                    # Colorear según resultado
                    if "correcta" in line.lower() or "verificada" in line.lower():
                        print(f"{SUCCESS}{line}{RESET}")
                    else:
                        print(f"{ERROR}{line}{RESET}")
                elif "Antivirus" in line:
                    # Colorear según resultado
                    if "limpio" in line.lower() or "seguro" in line.lower():
                        print(f"{SUCCESS}{line}{RESET}")
                    else:
                        print(f"{ERROR}{line}{RESET}")
                elif "Error" in line or "❌" in line:
                    print(f"{ERROR}{line}{RESET}")
                elif "✅" in line:
                    print(f"{SUCCESS}{line}{RESET}")
                else:
                    print(line)
        else:
            print_error(f"Error al verificar archivo: {response}")
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

def format_size(bytes):
    """Formatear tamaño en bytes a formato legible"""
    if bytes == 0:
        return "0 B"
    
    sizes = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes >= 1024 and i < len(sizes) - 1:
        bytes /= 1024
        i += 1
    
    return f"{bytes:.2f} {sizes[i]}"