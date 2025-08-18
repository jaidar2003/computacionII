#!/usr/bin/env python3
import cmd
import os
import sys
import readline
import atexit

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from cli.commands import auth, files, permissions
from cli.utils.visual import (
    print_success, print_error, print_info, print_warning, print_header,
    format_success, format_error, format_info, format_warning, 
    BOLD, RESET, SUCCESS, ERROR, WARNING, INFO, clear_screen
)
from cli.utils.config import CONFIG_DIR
from cli.utils.session import load_session

# Configurar historial de comandos
HISTORY_FILE = os.path.join(CONFIG_DIR, "history")
try:
    readline.read_history_file(HISTORY_FILE)
    readline.set_history_length(1000)
except FileNotFoundError:
    pass

atexit.register(readline.write_history_file, HISTORY_FILE)

class FileServerShell(cmd.Cmd):
    """CLI interactivo para el Servidor de Archivos"""
    
    intro = f"\n{BOLD}{INFO}Bienvenido al CLI interactivo del Servidor de Archivos{RESET}\n" \
            f"Escribe {BOLD}help{RESET} para ver los comandos disponibles.\n" \
            f"Escribe {BOLD}exit{RESET} para salir.\n"
    
    prompt = f"{BOLD}servidor> {RESET}"
    file = None
    
    # Lista de archivos para autocompletado
    file_list = []
    
    def preloop(self):
        """Acciones antes de iniciar el bucle de comandos"""
        # Actualizar el prompt según el estado de la sesión
        self._update_prompt()
    
    def _update_prompt(self):
        """Actualizar el prompt según el estado de la sesión"""
        session = load_session()
        if session:
            username = session.get("user", "Usuario")
            role = session.get("role", "usuario")
            role_color = WARNING if role == "admin" else INFO
            self.prompt = f"{BOLD}{SUCCESS}{username}{RESET}@{role_color}{role}{RESET}> "
        else:
            self.prompt = f"{BOLD}servidor> {RESET}"
    
    def _update_file_list(self):
        """Actualizar la lista de archivos para autocompletado"""
        # Solo intentar actualizar si hay una sesión activa
        session = load_session()
        if session:
            try:
                # Obtener lista de archivos del servidor
                files.list_files(silent=True)
                # La lista se actualizará en el próximo comando que la necesite
            except:
                pass
    
    def emptyline(self):
        """No hacer nada al presionar Enter sin comando"""
        pass
    
    def default(self, line):
        """Manejar comandos desconocidos"""
        print_error(f"Comando desconocido: {line}")
        print_info("Escribe 'help' para ver los comandos disponibles")
    
    # Comandos de autenticación
    def do_login(self, arg):
        """Iniciar sesión: login <usuario> <contraseña>"""
        args = arg.split()
        if len(args) != 2:
            print_error("Uso: login <usuario> <contraseña>")
            return
        
        auth.login(args[0], args[1])
        self._update_prompt()
    
    def do_register(self, arg):
        """Registrar nuevo usuario: register <usuario> <contraseña>"""
        args = arg.split()
        if len(args) != 2:
            print_error("Uso: register <usuario> <contraseña>")
            return
        
        auth.register(args[0], args[1])
    
    def do_logout(self, arg):
        """Cerrar sesión"""
        auth.logout()
        self._update_prompt()
    
    # Comandos de archivos
    def do_list(self, arg):
        """Listar archivos disponibles"""
        files.list_files()
        # Actualizar lista de archivos para autocompletado
        self._update_file_list()
    
    def do_ls(self, arg):
        """Alias para 'list'"""
        return self.do_list(arg)
    
    def do_upload(self, arg):
        """Subir archivo: upload <ruta_archivo>"""
        if not arg:
            print_error("Uso: upload <ruta_archivo>")
            return
        
        files.upload_file(arg)
        # Actualizar lista de archivos para autocompletado
        self._update_file_list()
    
    def complete_upload(self, text, line, begidx, endidx):
        """Autocompletar rutas de archivos locales"""
        # Obtener la parte de la ruta que ya se ha escrito
        path = line.split()[1] if len(line.split()) > 1 else ""
        
        if not path:
            path = "."
        
        # Si la ruta termina con un separador, buscar en ese directorio
        if path.endswith(os.sep):
            directory = path
            prefix = ""
        else:
            directory = os.path.dirname(path) or "."
            prefix = os.path.basename(path)
        
        try:
            # Obtener lista de archivos en el directorio
            files_in_dir = os.listdir(directory)
            # Filtrar por el prefijo
            return [f"{directory}{os.sep}{f}" for f in files_in_dir if f.startswith(prefix)]
        except:
            return []
    
    def do_download(self, arg):
        """Descargar archivo: download <nombre_archivo>"""
        if not arg:
            print_error("Uso: download <nombre_archivo>")
            return
        
        files.download_file(arg)
    
    def complete_download(self, text, line, begidx, endidx):
        """Autocompletar nombres de archivos en el servidor"""
        # Actualizar lista de archivos para autocompletado
        self._update_file_list()
        
        if not text:
            return self.file_list
        return [f for f in self.file_list if f.startswith(text)]
    
    def do_delete(self, arg):
        """Eliminar archivo: delete <nombre_archivo>"""
        if not arg:
            print_error("Uso: delete <nombre_archivo>")
            return
        
        files.delete_file(arg)
        # Actualizar lista de archivos para autocompletado
        self._update_file_list()
    
    def do_rm(self, arg):
        """Alias para 'delete'"""
        return self.do_delete(arg)
    
    def complete_delete(self, text, line, begidx, endidx):
        """Autocompletar nombres de archivos en el servidor"""
        return self.complete_download(text, line, begidx, endidx)
    
    complete_rm = complete_delete
    
    def do_rename(self, arg):
        """Renombrar archivo: rename <nombre_actual> <nombre_nuevo>"""
        args = arg.split()
        if len(args) != 2:
            print_error("Uso: rename <nombre_actual> <nombre_nuevo>")
            return
        
        files.rename_file(args[0], args[1])
        # Actualizar lista de archivos para autocompletado
        self._update_file_list()
    
    def complete_rename(self, text, line, begidx, endidx):
        """Autocompletar nombres de archivos en el servidor"""
        # Si es el primer argumento
        if len(line.split()) <= 2:
            return self.complete_download(text, line, begidx, endidx)
        return []
    
    def do_verify(self, arg):
        """Verificar archivo: verify [nombre_archivo]"""
        files.verify_file(arg if arg else None)
    
    def complete_verify(self, text, line, begidx, endidx):
        """Autocompletar nombres de archivos en el servidor"""
        return self.complete_download(text, line, begidx, endidx)
    
    # Comandos de permisos
    def do_request_permission(self, arg):
        """Solicitar cambio de permisos: request-permission <tipo_permiso>"""
        if arg not in ['usuario', 'admin']:
            print_error("Uso: request-permission <tipo_permiso>")
            print_info("Tipos de permiso válidos: 'usuario' o 'admin'")
            return
        
        permissions.request_permission(arg)
    
    def do_request(self, arg):
        """Alias para 'request-permission'"""
        return self.do_request_permission(arg)
    
    def complete_request_permission(self, text, line, begidx, endidx):
        """Autocompletar tipos de permiso"""
        options = ['usuario', 'admin']
        if not text:
            return options
        return [o for o in options if o.startswith(text)]
    
    complete_request = complete_request_permission
    
    def do_view_requests(self, arg):
        """Ver solicitudes de permisos"""
        permissions.view_requests()
    
    def do_requests(self, arg):
        """Alias para 'view-requests'"""
        return self.do_view_requests(arg)
    
    def do_approve(self, arg):
        """Aprobar/rechazar solicitud: approve <id_solicitud> <decisión>"""
        args = arg.split()
        if len(args) != 2 or args[1] not in ['aprobar', 'rechazar']:
            print_error("Uso: approve <id_solicitud> <decisión>")
            print_info("Decisiones válidas: 'aprobar' o 'rechazar'")
            return
        
        permissions.approve_request(args[0], args[1])
    
    def complete_approve(self, text, line, begidx, endidx):
        """Autocompletar decisiones"""
        # Si es el segundo argumento
        if len(line.split()) == 2:
            return []
        
        options = ['aprobar', 'rechazar']
        if not text:
            return options
        return [o for o in options if o.startswith(text)]
    
    def do_list_users(self, arg):
        """Listar usuarios del sistema (solo admin)"""
        permissions.list_users()
    
    def do_users(self, arg):
        """Alias para 'list-users'"""
        return self.do_list_users(arg)
    
    # Comandos de utilidad
    def do_clear(self, arg):
        """Limpiar la pantalla"""
        clear_screen()
    
    def do_cls(self, arg):
        """Alias para 'clear'"""
        return self.do_clear(arg)
    
    def do_status(self, arg):
        """Mostrar estado de la sesión"""
        session = load_session()
        if session:
            print_header("ESTADO DE LA SESIÓN")
            print(f"{INFO}Usuario:{RESET} {BOLD}{session.get('user', 'Desconocido')}{RESET}")
            
            role = session.get('role', 'desconocido')
            role_color = WARNING if role == "admin" else INFO
            print(f"{INFO}Rol:{RESET} {role_color}{role}{RESET}")
            
            print()
            print_info("Estás conectado al servidor y autenticado.")
        else:
            print_warning("No hay sesión activa.")
            print_info("Usa el comando 'login' para iniciar sesión.")
    
    def do_help(self, arg):
        """Mostrar ayuda sobre comandos"""
        if arg:
            # Ayuda para un comando específico
            super().do_help(arg)
        else:
            # Mostrar ayuda general categorizada
            print_header("AYUDA DEL CLI")
            
            print(f"\n{BOLD}{INFO}=== Comandos de Autenticación ==={RESET}")
            print(f"  {BOLD}login{RESET} <usuario> <contraseña> - Iniciar sesión")
            print(f"  {BOLD}register{RESET} <usuario> <contraseña> - Registrar nuevo usuario")
            print(f"  {BOLD}logout{RESET} - Cerrar sesión")
            
            print(f"\n{BOLD}{INFO}=== Comandos de Archivos ==={RESET}")
            print(f"  {BOLD}list{RESET} (ls) - Listar archivos")
            print(f"  {BOLD}upload{RESET} <ruta> - Subir archivo")
            print(f"  {BOLD}download{RESET} <archivo> - Descargar archivo")
            print(f"  {BOLD}delete{RESET} (rm) <archivo> - Eliminar archivo")
            print(f"  {BOLD}rename{RESET} <viejo> <nuevo> - Renombrar archivo")
            print(f"  {BOLD}verify{RESET} [archivo] - Verificar archivo(s)")
            
            print(f"\n{BOLD}{INFO}=== Comandos de Permisos ==={RESET}")
            print(f"  {BOLD}request-permission{RESET} (request) <tipo> - Solicitar permisos")
            print(f"  {BOLD}view-requests{RESET} (requests) - Ver solicitudes")
            print(f"  {BOLD}approve{RESET} <id> <decisión> - Aprobar/rechazar solicitud")
            print(f"  {BOLD}list-users{RESET} (users) - Listar usuarios (admin)")
            
            print(f"\n{BOLD}{INFO}=== Comandos de Utilidad ==={RESET}")
            print(f"  {BOLD}status{RESET} - Mostrar estado de la sesión")
            print(f"  {BOLD}clear{RESET} (cls) - Limpiar la pantalla")
            print(f"  {BOLD}help{RESET} [comando] - Mostrar ayuda")
            print(f"  {BOLD}exit{RESET} (quit) - Salir del programa")
    
    def do_exit(self, arg):
        """Salir del programa"""
        print_info("¡Hasta pronto! 👋")
        return True
    
    def do_quit(self, arg):
        """Alias para 'exit'"""
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        """Salir al presionar Ctrl+D"""
        print()  # Agregar una línea en blanco
        return self.do_exit(arg)

def main():
    """Iniciar el shell interactivo"""
    FileServerShell().cmdloop()

if __name__ == '__main__':
    main()