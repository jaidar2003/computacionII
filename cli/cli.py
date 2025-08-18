#!/usr/bin/env python3
import argparse
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from cli.commands import auth, files, permissions
from cli.utils.visual import print_info, print_error, print_header, BOLD, RESET

def main():
    parser = argparse.ArgumentParser(description='Cliente CLI para el Servidor de Archivos')
    
    # Agregar opción para modo interactivo
    parser.add_argument('-i', '--interactive', action='store_true', 
                        help='Iniciar en modo interactivo (shell)')
    parser.add_argument('--shell', action='store_true', 
                        help='Alias para --interactive')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando interactivo explícito
    interactive_parser = subparsers.add_parser('shell', help='Iniciar en modo interactivo (shell)')
    
    # Comandos de autenticación
    login_parser = subparsers.add_parser('login', help='Iniciar sesión')
    login_parser.add_argument('username', help='Nombre de usuario')
    login_parser.add_argument('password', help='Contraseña')
    
    register_parser = subparsers.add_parser('register', help='Registrar nuevo usuario')
    register_parser.add_argument('username', help='Nombre de usuario')
    register_parser.add_argument('password', help='Contraseña')
    
    logout_parser = subparsers.add_parser('logout', help='Cerrar sesión')
    
    # Comandos de archivos
    list_parser = subparsers.add_parser('list', help='Listar archivos')
    list_parser.add_argument('--silent', action='store_true', help=argparse.SUPPRESS)
    
    upload_parser = subparsers.add_parser('upload', help='Subir archivo')
    upload_parser.add_argument('file_path', help='Ruta del archivo a subir')
    
    download_parser = subparsers.add_parser('download', help='Descargar archivo')
    download_parser.add_argument('filename', help='Nombre del archivo a descargar')
    
    delete_parser = subparsers.add_parser('delete', help='Eliminar archivo')
    delete_parser.add_argument('filename', help='Nombre del archivo a eliminar')
    
    rename_parser = subparsers.add_parser('rename', help='Renombrar archivo')
    rename_parser.add_argument('old_name', help='Nombre actual del archivo')
    rename_parser.add_argument('new_name', help='Nuevo nombre del archivo')
    
    verify_parser = subparsers.add_parser('verify', help='Verificar archivo')
    verify_parser.add_argument('filename', nargs='?', help='Nombre del archivo a verificar (opcional)')
    
    # Comandos de permisos
    request_parser = subparsers.add_parser('request-permission', help='Solicitar cambio de permisos')
    request_parser.add_argument('permission_type', choices=['usuario', 'admin'], help='Tipo de permiso')
    
    view_requests_parser = subparsers.add_parser('view-requests', help='Ver solicitudes de permisos')
    
    approve_parser = subparsers.add_parser('approve', help='Aprobar/rechazar solicitud (solo admin)')
    approve_parser.add_argument('request_id', help='ID de la solicitud')
    approve_parser.add_argument('decision', choices=['aprobar', 'rechazar'], help='Decisión')
    
    list_users_parser = subparsers.add_parser('list-users', help='Listar usuarios (solo admin)')
    
    # Comandos de utilidad
    status_parser = subparsers.add_parser('status', help='Mostrar estado de la sesión')
    
    # Alias comunes
    subparsers.add_parser('ls', help='Alias para list').set_defaults(command='list')
    subparsers.add_parser('rm', help='Alias para delete').add_argument('filename')
    
    args = parser.parse_args()
    
    # Verificar si se debe iniciar en modo interactivo
    if args.interactive or args.shell or args.command == 'shell':
        try:
            from cli.interactive import main as interactive_main
            print_header("MODO INTERACTIVO")
            print_info(f"Iniciando shell interactivo. Usa {BOLD}help{RESET} para ver los comandos disponibles.")
            interactive_main()
            return
        except ImportError as e:
            print_error(f"No se pudo iniciar el modo interactivo: {str(e)}")
            print_info("Continuando en modo de línea de comandos...")
    
    # Si no hay comando y no se especificó modo interactivo, mostrar ayuda
    if not args.command:
        print_header("CLI DEL SERVIDOR DE ARCHIVOS")
        print_info(f"Usa {BOLD}--interactive{RESET} o {BOLD}shell{RESET} para iniciar en modo interactivo")
        print_info(f"O especifica un comando para ejecutar una acción específica")
        parser.print_help()
        sys.exit(0)
    
    # Ejecutar el comando correspondiente
    if args.command == 'login':
        auth.login(args.username, args.password)
    elif args.command == 'register':
        auth.register(args.username, args.password)
    elif args.command == 'logout':
        auth.logout()
    elif args.command == 'list' or args.command == 'ls':
        files.list_files(getattr(args, 'silent', False))
    elif args.command == 'upload':
        files.upload_file(args.file_path)
    elif args.command == 'download':
        files.download_file(args.filename)
    elif args.command == 'delete' or args.command == 'rm':
        files.delete_file(args.filename)
    elif args.command == 'rename':
        files.rename_file(args.old_name, args.new_name)
    elif args.command == 'verify':
        files.verify_file(args.filename)
    elif args.command == 'request-permission':
        permissions.request_permission(args.permission_type)
    elif args.command == 'view-requests':
        permissions.view_requests()
    elif args.command == 'approve':
        permissions.approve_request(args.request_id, args.decision)
    elif args.command == 'list-users':
        permissions.list_users()
    elif args.command == 'status':
        # Mostrar estado de la sesión
        session = auth.load_session()
        if session:
            print_header("ESTADO DE LA SESIÓN")
            print(f"Usuario: {BOLD}{session.get('user', 'Desconocido')}{RESET}")
            print(f"Rol: {BOLD}{session.get('role', 'desconocido')}{RESET}")
        else:
            print_error("No hay sesión activa")
            print_info("Usa el comando 'login' para iniciar sesión")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()