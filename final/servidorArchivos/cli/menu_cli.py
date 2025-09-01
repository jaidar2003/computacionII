#!/usr/bin/env python3
import os
import sys
import getpass

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from .commands import auth, files, permissions
from .utils.visual import print_info, print_error, print_header, print_success, print_warning
from .utils.visual import BOLD, RESET, SUCCESS, ERROR, WARNING, INFO, clear_screen
from .utils.session import load_session, clear_session

def mostrar_menu_principal():
    """Muestra el menú principal del CLI"""
    clear_screen()
    print_header("SERVIDOR DE ARCHIVOS - MENÚ PRINCIPAL")
    
    session = load_session()
    if session:
        username = session.get("user", "Usuario")
        role = session.get("role", "usuario")
        print(f"{INFO}Sesión activa: {BOLD}{username}{RESET} ({role})\n")
    
    print(f"{BOLD}1.{RESET} Iniciar sesión")
    print(f"{BOLD}2.{RESET} Registrarse")
    print(f"{BOLD}3.{RESET} Salir")
    
    if session:
        print(f"\n{BOLD}4.{RESET} Listar archivos")
        print(f"{BOLD}5.{RESET} Subir archivo")
        print(f"{BOLD}6.{RESET} Descargar archivo")
        print(f"{BOLD}7.{RESET} Eliminar archivo")
        print(f"{BOLD}8.{RESET} Renombrar archivo")
        print(f"{BOLD}9.{RESET} Verificar archivo")
        print(f"{BOLD}10.{RESET} Cerrar sesión")
        
        if role == "admin":
            print(f"\n{BOLD}11.{RESET} Listar usuarios")
            print(f"{BOLD}12.{RESET} Ver solicitudes de permisos")
            print(f"{BOLD}13.{RESET} Aprobar/rechazar solicitud")
        else:
            print(f"\n{BOLD}11.{RESET} Solicitar permisos de administrador")
            print(f"{BOLD}12.{RESET} Ver mis solicitudes de permisos")

def iniciar_sesion():
    """Función para iniciar sesión"""
    clear_screen()
    print_header("INICIAR SESIÓN")
    
    username = input(f"{BOLD}Usuario: {RESET}")
    password = getpass.getpass(f"{BOLD}Contraseña: {RESET}")
    
    if not username or not password:
        print_error("Usuario y contraseña son obligatorios")
        input("\nPresiona Enter para continuar...")
        return
    
    auth.login(username, password)
    input("\nPresiona Enter para continuar...")

def registrarse():
    """Función para registrar un nuevo usuario"""
    clear_screen()
    print_header("REGISTRARSE")
    
    username = input(f"{BOLD}Usuario: {RESET}")
    password = getpass.getpass(f"{BOLD}Contraseña: {RESET}")
    confirm_password = getpass.getpass(f"{BOLD}Confirmar contraseña: {RESET}")
    
    if not username or not password:
        print_error("Usuario y contraseña son obligatorios")
        input("\nPresiona Enter para continuar...")
        return
    
    if password != confirm_password:
        print_error("Las contraseñas no coinciden")
        input("\nPresiona Enter para continuar...")
        return
    
    auth.register(username, password)
    input("\nPresiona Enter para continuar...")

def listar_archivos():
    """Función para listar archivos"""
    clear_screen()
    print_header("LISTAR ARCHIVOS")
    
    files.list_files()
    input("\nPresiona Enter para continuar...")

def subir_archivo():
    """Función para subir un archivo"""
    clear_screen()
    print_header("SUBIR ARCHIVO")
    
    file_path = input(f"{BOLD}Ruta del archivo: {RESET}")
    
    if not file_path:
        print_error("La ruta del archivo es obligatoria")
        input("\nPresiona Enter para continuar...")
        return
    
    files.upload_file(file_path)
    input("\nPresiona Enter para continuar...")

def descargar_archivo():
    """Función para descargar un archivo"""
    clear_screen()
    print_header("DESCARGAR ARCHIVO")
    
    # Primero mostrar la lista de archivos disponibles
    print_info("Archivos disponibles:")
    file_list = files.list_files(silent=True)
    
    if not file_list:
        print_warning("No se pudo obtener la lista en modo silencioso. Reintentando...")
        files.list_files(silent=False)
    
    filename = input(f"\n{BOLD}Nombre del archivo a descargar: {RESET}")
    
    if not filename:
        print_error("El nombre del archivo es obligatorio")
        input("\nPresiona Enter para continuar...")
        return
    
    files.download_file(filename)
    input("\nPresiona Enter para continuar...")

def eliminar_archivo():
    """Función para eliminar un archivo"""
    clear_screen()
    print_header("ELIMINAR ARCHIVO")
    
    # Primero mostrar la lista de archivos disponibles
    print_info("Archivos disponibles:")
    file_list = files.list_files(silent=True)
    
    if not file_list:
        print_warning("No se pudo obtener la lista en modo silencioso. Reintentando...")
        files.list_files(silent=False)
    
    filename = input(f"\n{BOLD}Nombre del archivo a eliminar: {RESET}")
    
    if not filename:
        print_error("El nombre del archivo es obligatorio")
        input("\nPresiona Enter para continuar...")
        return
    
    files.delete_file(filename)
    input("\nPresiona Enter para continuar...")

def renombrar_archivo():
    """Función para renombrar un archivo"""
    clear_screen()
    print_header("RENOMBRAR ARCHIVO")
    
    # Primero mostrar la lista de archivos disponibles
    print_info("Archivos disponibles:")
    file_list = files.list_files(silent=True)
    
    if not file_list:
        print_warning("No se pudo obtener la lista en modo silencioso. Reintentando...")
        files.list_files(silent=False)
    
    old_name = input(f"\n{BOLD}Nombre actual del archivo: {RESET}")
    
    if not old_name:
        print_error("El nombre actual del archivo es obligatorio")
        input("\nPresiona Enter para continuar...")
        return
    
    new_name = input(f"{BOLD}Nuevo nombre del archivo: {RESET}")
    
    if not new_name:
        print_error("El nuevo nombre del archivo es obligatorio")
        input("\nPresiona Enter para continuar...")
        return
    
    files.rename_file(old_name, new_name)
    input("\nPresiona Enter para continuar...")

def verificar_archivo():
    """Función para verificar un archivo"""
    clear_screen()
    print_header("VERIFICAR ARCHIVO")

    # Mostrar SIEMPRE la lista visible (no silenciosa) y obtener nombres en una sola llamada
    print_info("Archivos disponibles:")
    file_list = files.list_files(silent=False) or []  # imprime tabla y devuelve nombres

    # Filtrar .hash y .sha256
    file_list = [
        f for f in file_list
        if not (f.endswith('.hash') or f.endswith('.sha256'))
    ]

    if not file_list:
        print_warning("No se pudo construir la lista para selección rápida. Puedes escribir el nombre manualmente o verificar todos.")
    else:
        # Muestra selección rápida por número
        print(f"\n{BOLD}Opciones rápidas:{RESET}")
        for idx, name in enumerate(file_list, start=1):
            print(f"{idx}. {name}")
        print("0. Verificar TODOS los archivos")

    # Menú por letras para evitar ambigüedad con los números de arriba
    print(f"\n{BOLD}Opciones:{RESET}")
    print("A. Verificar un archivo escribiendo el nombre")
    print("T. Verificar todos los archivos")
    print("Q. Volver")

    option = input(f"\n{BOLD}Selecciona (número de archivo, 0, A/T/Q): {RESET}").strip()

    # ¿Número? → selección rápida
    if option.isdigit():
        num = int(option)
        if num == 0:
            files.verify_file()  # todos
            input("\nPresiona Enter para continuar...")
            return
        if 1 <= num <= len(file_list):
            filename = file_list[num - 1]
            files.verify_file(filename)
            input("\nPresiona Enter para continuar...")
            return
        # número inválido: sigue a evaluar letras

    # ¿Letra? → acciones manuales
    opt = option.upper()
    if opt == "A":
        filename = input(f"{BOLD}Nombre del archivo a verificar: {RESET}").strip()
        if not filename:
            print_error("El nombre del archivo es obligatorio")
        else:
            files.verify_file(filename)
    elif opt == "T":
        files.verify_file()
    elif opt == "Q":
        print_info("Operación cancelada.")
    else:
        print_error("Opción inválida")

    input("\nPresiona Enter para continuar...")

def cerrar_sesion():
    """Función para cerrar sesión"""
    clear_screen()
    print_header("CERRAR SESIÓN")
    
    auth.logout()
    input("\nPresiona Enter para continuar...")

def listar_usuarios():
    """Función para listar usuarios (solo admin)"""
    clear_screen()
    print_header("LISTAR USUARIOS")
    
    permissions.list_users()
    input("\nPresiona Enter para continuar...")

def ver_solicitudes():
    """Función para ver solicitudes de permisos"""
    clear_screen()
    print_header("VER SOLICITUDES DE PERMISOS")
    
    permissions.view_requests()
    input("\nPresiona Enter para continuar...")

def aprobar_solicitud():
    """Función para aprobar/rechazar solicitudes (solo admin)"""
    clear_screen()
    print_header("APROBAR/RECHAZAR SOLICITUD")
    
    # Primero mostrar las solicitudes pendientes
    permissions.view_requests()
    
    request_id = input(f"\n{BOLD}ID de la solicitud: {RESET}")
    
    if not request_id:
        print_error("El ID de la solicitud es obligatorio")
        input("\nPresiona Enter para continuar...")
        return
    
    print(f"\n{BOLD}Opciones:{RESET}")
    print(f"1. Aprobar")
    print(f"2. Rechazar")
    
    option = input(f"\n{BOLD}Selecciona una opción (1-2): {RESET}")
    
    if option == "1":
        permissions.approve_request(request_id, "aprobar")
    elif option == "2":
        permissions.approve_request(request_id, "rechazar")
    else:
        print_error("Opción inválida")
    
    input("\nPresiona Enter para continuar...")

def solicitar_permisos():
    """Función para solicitar permisos de administrador"""
    clear_screen()
    print_header("SOLICITAR PERMISOS DE ADMINISTRADOR")
    
    permissions.request_permission("admin")
    input("\nPresiona Enter para continuar...")

def main():
    """Función principal del CLI"""
    while True:
        mostrar_menu_principal()
        
        session = load_session()
        
        try:
            opcion = input(f"\n{BOLD}Selecciona una opción: {RESET}")
            
            if not session:
                # Menú sin sesión
                if opcion == "1":
                    iniciar_sesion()
                elif opcion == "2":
                    registrarse()
                elif opcion == "3":
                    print_info("¡Hasta pronto! 👋")
                    break
                else:
                    print_error("Opción inválida")
                    input("\nPresiona Enter para continuar...")
            else:
                # Menú con sesión
                role = session.get("role", "usuario")
                
                if opcion == "1":
                    iniciar_sesion()
                elif opcion == "2":
                    registrarse()
                elif opcion == "3":
                    print_info("¡Hasta pronto! 👋")
                    break
                elif opcion == "4":
                    listar_archivos()
                elif opcion == "5":
                    subir_archivo()
                elif opcion == "6":
                    descargar_archivo()
                elif opcion == "7":
                    eliminar_archivo()
                elif opcion == "8":
                    renombrar_archivo()
                elif opcion == "9":
                    verificar_archivo()
                elif opcion == "10":
                    cerrar_sesion()
                elif opcion == "11":
                    if role == "admin":
                        listar_usuarios()
                    else:
                        solicitar_permisos()
                elif opcion == "12":
                    ver_solicitudes()
                elif opcion == "13" and role == "admin":
                    aprobar_solicitud()
                else:
                    print_error("Opción inválida")
                    input("\nPresiona Enter para continuar...")
        except KeyboardInterrupt:
            print_info("\n\n¡Hasta pronto! 👋")
            break
        except Exception as e:
            print_error(f"Error inesperado: {str(e)}")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()