#!/usr/bin/env python3
import argparse
import sys
import os
from commands import auth, files, permissions

def main():
    parser = argparse.ArgumentParser(description='Cliente CLI para el Servidor de Archivos')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
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
    
    args = parser.parse_args()
    
    # Ejecutar el comando correspondiente
    if args.command == 'login':
        auth.login(args.username, args.password)
    elif args.command == 'register':
        auth.register(args.username, args.password)
    elif args.command == 'logout':
        auth.logout()
    elif args.command == 'list':
        files.list_files()
    elif args.command == 'upload':
        files.upload_file(args.file_path)
    elif args.command == 'download':
        files.download_file(args.filename)
    elif args.command == 'delete':
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
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()