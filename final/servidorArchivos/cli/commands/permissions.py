import sys
import socket
from ..utils import config
from ..utils.session import load_session, check_auth
from ..utils.connection import create_ssl_connection, send_command, receive_prompt, send_response
from ..utils.visual import (
    print_success, print_error, print_info, print_warning, print_header,
    format_success, format_error, format_info, format_warning, 
    print_table_header, print_table_row, BOLD, RESET, SUCCESS, ERROR, WARNING, INFO
)

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
    
    # Enviar contraseña (usar la contraseña real de la sesión)
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
def request_permission(permission_type):
    """Solicitar cambio de permisos"""
    # Validar el tipo de permiso
    if permission_type not in ['usuario', 'admin']:
        print_error(f"Tipo de permiso inválido: {permission_type}")
        print_info("Los tipos de permiso válidos son: 'usuario' o 'admin'")
        return
    
    print_info(f"Conectando al servidor para solicitar permisos de {BOLD}{permission_type}{RESET}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        print_info(f"Solicitando permisos de {BOLD}{permission_type}{RESET}...")
        
        # Enviar comando SOLICITAR_PERMISOS
        response = send_command(connection, f"SOLICITAR_PERMISOS {permission_type}")
        
        if "✅" in response:
            print_success(f"Solicitud de permisos de {BOLD}{permission_type}{RESET} enviada correctamente")
            print_info("Un administrador revisará tu solicitud pronto")
        else:
            print_error(f"Error al solicitar permisos: {response}")
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def view_requests():
    """Ver solicitudes de permisos"""
    print_info("Conectando al servidor para ver solicitudes de permisos...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        print_info("Obteniendo solicitudes de permisos...")
        
        # Enviar comando VER_SOLICITUDES
        response = send_command(connection, "VER_SOLICITUDES")
        
        # Cerrar conexión
        connection.close()
        
        # Procesar la respuesta para mostrarla de forma más amigable
        if "No hay solicitudes" in response:
            print_warning("No hay solicitudes de permisos pendientes.")
            return
        
        # Extraer información de la respuesta
        # La respuesta tiene un formato como:
        # "✅ Solicitudes de permisos:\nID: 1, Usuario: user1, Permiso: admin, Fecha: 2023-01-01\nID: 2, Usuario: user2, Permiso: usuario, Fecha: 2023-01-02"
        lines = response.split('\n')
        
        # Mostrar encabezado
        print_header("SOLICITUDES DE PERMISOS")
        
        # Determinar si el usuario es admin para mostrar columnas diferentes
        session = load_session()
        is_admin = session.get("role") == "admin"
        
        # Definir anchos de columna y encabezados según el rol
        if is_admin:
            widths = [5, 20, 15, 25]
            headers = ["ID", "Usuario", "Permiso", "Fecha"]
        else:
            widths = [5, 15, 15, 25]
            headers = ["ID", "Permiso", "Estado", "Fecha"]
        
        # Mostrar encabezado de tabla
        print_table_header(headers, widths)
        
        # Procesar cada línea (saltando la primera que es el encabezado)
        for line in lines[1:]:
            if not line.strip():
                continue
                
            # Extraer información de la línea
            try:
                # Formato esperado: "ID: 1, Usuario: user1, Permiso: admin, Fecha: 2023-01-01"
                parts = {}
                for part in line.split(', '):
                    if ': ' in part:
                        key, value = part.split(': ', 1)
                        parts[key.lower()] = value
                
                # Mostrar fila según el rol
                if is_admin:
                    print_table_row([
                        parts.get('id', ''),
                        parts.get('usuario', ''),
                        parts.get('permiso', ''),
                        parts.get('fecha', '')
                    ], widths)
                else:
                    print_table_row([
                        parts.get('id', ''),
                        parts.get('permiso', ''),
                        parts.get('estado', 'Pendiente'),
                        parts.get('fecha', '')
                    ], widths)
            except Exception:
                # Si no se puede parsear, mostrar la línea completa
                print(line)
        
        # Mostrar instrucciones adicionales
        if is_admin:
            print()
            print_info(f"Para aprobar una solicitud: {BOLD}approve ID aprobar{RESET}")
            print_info(f"Para rechazar una solicitud: {BOLD}approve ID rechazar{RESET}")
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def approve_request(request_id, decision):
    """Aprobar o rechazar una solicitud de permisos (solo admin)"""
    session = load_session()
    
    # Verificar que el usuario es administrador
    if session.get("role") != "admin":
        print_error("Solo los administradores pueden aprobar o rechazar solicitudes")
        print_info("Si necesitas permisos de administrador, usa 'request-permission admin'")
        return
    
    # Validar la decisión
    if decision not in ['aprobar', 'rechazar']:
        print_error(f"Decisión inválida: {decision}")
        print_info("Las decisiones válidas son: 'aprobar' o 'rechazar'")
        return
    
    # Mostrar confirmación
    action_text = "aprobar" if decision == "aprobar" else "rechazar"
    print_warning(f"¿Estás seguro de que deseas {action_text} la solicitud {BOLD}#{request_id}{RESET}?")
    confirm = input(f"{WARNING}Esta acción no se puede deshacer (s/n): {RESET}")
    
    if confirm.lower() != 's':
        print_info("Operación cancelada")
        return
    
    print_info(f"Conectando al servidor para {action_text} la solicitud #{request_id}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        print_info(f"{action_text.capitalize()} solicitud #{request_id}...")
        
        # Enviar comando APROBAR_PERMISOS
        response = send_command(connection, f"APROBAR_PERMISOS {request_id} {decision}")
        
        if "✅" in response:
            print_success(f"Solicitud #{request_id} {action_text}da correctamente")
            print_info("Los cambios de permisos se aplicarán inmediatamente")
        else:
            print_error(f"Error al {action_text} solicitud: {response}")
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

@check_auth
def list_users():
    """Listar usuarios del sistema (solo admin)"""
    session = load_session()
    
    # Verificar que el usuario es administrador
    if session.get("role") != "admin":
        print_error("Solo los administradores pueden listar usuarios")
        print_info("Si necesitas permisos de administrador, usa 'request-permission admin'")
        return
    
    print_info("Conectando al servidor para obtener la lista de usuarios...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Autenticar con la sesión guardada
        _authenticate_with_session(connection)
        
        print_info("Obteniendo lista de usuarios...")
        
        # Enviar comando LISTAR_USUARIOS
        response = send_command(connection, "LISTAR_USUARIOS")
        
        # Cerrar conexión
        connection.close()
        
        # Procesar la respuesta para mostrarla de forma más amigable
        if "No hay usuarios" in response:
            print_warning("No hay usuarios registrados en el sistema.")
            return
        
        # Extraer información de la respuesta
        # La respuesta tiene un formato como:
        # "✅ Usuarios del sistema:\nID: 1, Usuario: admin, Permiso: admin\nID: 2, Usuario: user1, Permiso: usuario"
        lines = response.split('\n')
        
        # Mostrar encabezado
        print_header("USUARIOS DEL SISTEMA")
        
        # Definir anchos de columna
        widths = [5, 25, 15]
        
        # Mostrar encabezado de tabla
        print_table_header(["ID", "Usuario", "Permiso"], widths)
        
        # Procesar cada línea (saltando la primera que es el encabezado)
        for line in lines[1:]:
            raw = line.strip()
            if not raw:
                continue

            try:
                # Normalizar y limpiar bullets/emojis comunes
                cleaned = raw
                for token in ["•", "👤", "👑", "👥", "📊"]:
                    cleaned = cleaned.replace(token, "")
                cleaned = cleaned.strip()

                # Separar segmentos: soportar " | " o ", "
                if " | " in cleaned:
                    segments = [seg.strip() for seg in cleaned.split("|")]
                else:
                    segments = [seg.strip() for seg in cleaned.split(", ")]

                kv = {}
                for seg in segments:
                    if ":" in seg:
                        k, v = seg.split(":", 1)
                        k = k.strip().lower()
                        v = v.strip()
                        # Normalizar claves
                        if k.startswith("id"):
                            kv['id'] = v
                        elif k.startswith("usuario"):
                            kv['usuario'] = v
                        elif k.startswith("permiso"):
                            kv['permiso'] = v

                user_id = kv.get('id', '')
                username = kv.get('usuario', '')
                permission = kv.get('permiso', '')

                # Destacar el usuario actual
                if username == session.get("user") and username:
                    username = f"{BOLD}{username} (tú){RESET}"

                # Colorear el permiso si presente
                if permission:
                    if permission.lower() == 'admin':
                        permission = f"{WARNING}{permission}{RESET}"
                    else:
                        permission = f"{INFO}{permission}{RESET}"

                # Si logramos extraer algo significativo, imprimir fila; si no, fallback
                if user_id or username or permission:
                    print_table_row([user_id, username, permission], widths)
                else:
                    print(raw)
            except Exception:
                # Si no se puede parsear, mostrar la línea completa
                print(raw)
        
        # Mostrar instrucciones adicionales
        print()
        print_info("Para gestionar permisos, usa los comandos:")
        print_info(f"  {BOLD}view-requests{RESET} - Ver solicitudes de permisos")
        print_info(f"  {BOLD}approve ID decision{RESET} - Aprobar/rechazar solicitudes")
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()