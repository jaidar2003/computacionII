import os
import json
from ..utils import config
from ..utils.session import save_session, load_session, clear_session
from ..utils.connection import create_ssl_connection, receive_prompt, send_response
from ..utils.visual import (
    print_success, print_error, print_info, print_warning, print_header,
    format_success, format_error, format_info, format_warning, BOLD, RESET
)

def login(username, password):
    """Iniciar sesión en el servidor"""
    print_info(f"Conectando al servidor {config.SERVER_HOST}:{config.SERVER_PORT}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Recibir mensaje de bienvenida
        welcome = receive_prompt(connection)
        print_header("SERVIDOR DE ARCHIVOS")
        print(welcome)
        
        # Recibir prompt de usuario
        user_prompt = receive_prompt(connection)
        print(f"{BOLD}{user_prompt}{RESET}")
        
        # Enviar nombre de usuario
        print_info(f"Autenticando como {BOLD}{username}{RESET}...")
        send_response(connection, username)
        
        # Recibir prompt de contraseña
        pass_prompt = receive_prompt(connection)
        print(f"{BOLD}{pass_prompt}{RESET}")
        
        # Enviar contraseña
        send_response(connection, password)
        
        # Recibir resultado de autenticación
        auth_result = receive_prompt(connection)
        
        # Si la autenticación fue exitosa, guardar sesión
        if "✅ Autenticación exitosa" in auth_result:
            # Extraer permisos del mensaje
            permisos = "admin" if "admin" in auth_result.lower() else "usuario"
            
            save_session({
                "user": username,
                "role": permisos,
                "password": password
            })
            
            print_success(f"Sesión iniciada como {BOLD}{username}{RESET} ({permisos})")
            print_info("Ahora puedes usar comandos como 'list', 'upload', etc.")
        else:
            print_error("Autenticación fallida. Verifica tus credenciales.")
            print(auth_result)
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

def register(username, password):
    """Registrar un nuevo usuario"""
    print_info(f"Conectando al servidor {config.SERVER_HOST}:{config.SERVER_PORT}...")
    
    # Crear conexión SSL
    connection = create_ssl_connection(config.SERVER_HOST, config.SERVER_PORT)
    if not connection:
        print_error("No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
        return
    
    try:
        # Recibir mensaje de bienvenida
        welcome = receive_prompt(connection)
        print_header("REGISTRO DE USUARIO")
        print(welcome)
        
        # Recibir prompt de usuario
        user_prompt = receive_prompt(connection)
        print(f"{BOLD}{user_prompt}{RESET}")
        
        # Enviar comando de registro
        print_info(f"Registrando usuario {BOLD}{username}{RESET}...")
        send_response(connection, f"REGISTRAR {username} {password}")
        
        # Recibir resultado del registro
        register_result = receive_prompt(connection)
        
        if "✅" in register_result:
            print_success(f"Usuario {BOLD}{username}{RESET} registrado correctamente")
            print_info("Ahora puedes iniciar sesión con el comando 'login'")
        else:
            print_error("Error al registrar usuario")
            print(register_result)
        
        # Cerrar conexión
        connection.close()
    
    except Exception as e:
        print_error(f"Error de conexión: {str(e)}")
        if connection:
            connection.close()

def logout():
    """Cerrar sesión"""
    print_info("Verificando sesión...")
    session = load_session()
    
    if not session:
        print_warning("No hay sesión activa. No es necesario cerrar sesión.")
        return
    
    username = session.get("user", "Usuario")
    role = session.get("role", "desconocido")
    
    # Limpiar la sesión local
    clear_session()
    print_success(f"Sesión de {BOLD}{username}{RESET} ({role}) cerrada correctamente")
    print_info("Hasta pronto! 👋")