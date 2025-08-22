#!/usr/bin/env python3
import os
import sys
import getpass

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from ..commands import auth
from ..utils.visual import print_info, print_error, print_header, print_success, print_warning
from ..utils.visual import BOLD, RESET, SUCCESS, ERROR, WARNING, INFO, clear_screen
from ..utils.session import load_session, clear_session

def mostrar_menu_simple():
    """Muestra un menú simplificado con solo las opciones básicas"""
    clear_screen()
    print_header("SERVIDOR DE ARCHIVOS - MENÚ SIMPLIFICADO")
    
    session = load_session()
    if session:
        username = session.get("user", "Usuario")
        role = session.get("role", "usuario")
        print(f"{INFO}Sesión activa: {BOLD}{username}{RESET} ({role})\n")
    
    print(f"{BOLD}1.{RESET} Iniciar sesión")
    print(f"{BOLD}2.{RESET} Registrarse")
    print(f"{BOLD}3.{RESET} Salir")

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

def main():
    """Función principal del menú simplificado"""
    while True:
        mostrar_menu_simple()
        
        try:
            opcion = input(f"\n{BOLD}Selecciona una opción: {RESET}")
            
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
        except KeyboardInterrupt:
            print_info("\n\n¡Hasta pronto! 👋")
            break
        except Exception as e:
            print_error(f"Error inesperado: {str(e)}")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()