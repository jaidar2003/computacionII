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
        
        # Recibir el prompt de comando
        command_prompt = receive_prompt(connection)
        
        # Enviar comando LISTAR
        send_response(connection, "LISTAR")
        
        # Recibir respuesta del comando
        response = receive_prompt(connection)
        
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
        
        # Recibir el prompt de comando
        command_prompt = receive_prompt(connection)
        
        # Implementar nuestra propia función de subida con barra de progreso
        try:
            # Enviar comando SUBIR con el nombre del archivo
            command = f'SUBIR "{filename}"'
            send_response(connection, command)
            
            # Recibir respuesta inicial (si el servidor está listo para recibir)
            initial_response = connection.recv(1024).decode('utf-8').strip()
            if "listo para recibir" not in initial_response.lower():
                print_error(f"Error al iniciar la subida: {initial_response}")
                connection.close()
                return
            
            # Enviar el tamaño del archivo primero (como espera el servidor)
            connection.sendall(str(file_size).encode("utf-8"))
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
        
        # Ahora el servidor está esperando comandos en el bucle _procesar_comandos
        # Recibir el prompt de comando
        command_prompt = receive_prompt(connection)
        
        # Enviar comando DESCARGAR
        command = f'DESCARGAR "{filename}"'
        send_response(connection, command)
        
        # Recibir mensaje de confirmación del servidor
        server_response = connection.recv(4096).decode('utf-8').strip()
        
        # Si el servidor reporta un error, mostrarlo y salir
        if server_response.startswith("❌") or server_response.startswith("⚠️"):
            print_error(f"Error del servidor: {server_response}")
            connection.close()
            return
        
        # Si el servidor está listo para enviar, extraer el tamaño del archivo
        if "✅ Listo para enviar" in server_response:
            # Extraer tamaño del archivo del mensaje
            # Formato: "✅ Listo para enviar 'archivo.txt' (12345 bytes)"
            try:
                size_start = server_response.find("(") + 1
                size_end = server_response.find(" bytes)")
                file_size = int(server_response[size_start:size_end])
            except (ValueError, IndexError):
                file_size = None
            
            # Enviar confirmación al servidor
            connection.sendall("LISTO".encode('utf-8'))
            
            # Recibir el archivo con barra de progreso
            file_data = b''
            bytes_received = 0
            
            # Crear barra de progreso con el tamaño real
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Descargando {filename}", 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
                while bytes_received < file_size:
                    # Usar chunks más pequeños para actualizaciones más fluidas
                    chunk_size = min(4096, file_size - bytes_received)
                    chunk = connection.recv(chunk_size)
                    if not chunk:
                        break
                    
                    file_data += chunk
                    bytes_received += len(chunk)
                    pbar.update(len(chunk))
                    
                    # Pequeño delay para hacer la actualización más visible en archivos pequeños
                    if file_size < 1024 * 1024:  # Solo para archivos menores a 1MB
                        import time
                        time.sleep(0.001)  # 1ms delay
            
            # Determinar la ruta de descarga
            download_path = filename  # Por defecto, directorio actual
            if config.CLIENTE_DIR:
                # Crear directorio de descargas si no existe
                os.makedirs(config.CLIENTE_DIR, exist_ok=True)
                download_path = os.path.join(config.CLIENTE_DIR, filename)
            
            # Guardar archivo
            with open(download_path, 'wb') as f:
                f.write(file_data)
            
            # Enviar confirmación final al servidor
            connection.sendall("✅ Archivo recibido correctamente".encode('utf-8'))
            
            print_success(f"Archivo {BOLD}{filename}{RESET} descargado correctamente ({format_size(len(file_data))})")
            if config.CLIENTE_DIR:
                print_info(f"Guardado en: {BOLD}{download_path}{RESET}")
        else:
            print_error(f"Respuesta inesperada del servidor: {server_response}")
        
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