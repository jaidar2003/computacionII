# cli/interface.py

def mostrar_banner():
    print("\n\033[1;36m" + "\u2554" + "\u2550"*50 + "\u2557\033[0m")
    print("\033[1;36m\u2551\033[0m" + "\033[1;33mCLIENTE DE ARCHIVOS SEGURO\033[0m".center(50) + "\033[1;36m\u2551\033[0m")
    print("\033[1;36m" + "\u255A" + "\u2550"*50 + "\u255D\033[0m\n")

def mostrar_menu_principal():
    print("\n\033[1;36m\u2554" + "\u2550"*40 + "\u2557\033[0m")
    print("\033[1;36m\u2551\033[0m\033[1;33m  Opciones:\033[0m".ljust(39) + "\033[1;36m\u2551\033[0m")
    print("\033[1;36m\u2551\033[0m  [1] Iniciar sesión".ljust(39) + "\033[1;36m\u2551\033[0m")
    print("\033[1;36m\u2551\033[0m  [2] Registrarse".ljust(39) + "\033[1;36m\u2551\033[0m")
    print("\033[1;36m\u2551\033[0m  [3] Salir".ljust(39) + "\033[1;36m\u2551\033[0m")
    print("\033[1;36m\u255A" + "\u2550"*40 + "\u255D\033[0m")

def mostrar_comandos_disponibles(permisos):
    print("\n\033[1;34mComandos disponibles:\033[0m")
    print("  - LISTAR")
    print("  - CREAR [archivo]")
    print("  - SUBIR [archivo]")
    print("  - DESCARGAR [archivo]")
    print("  - ELIMINAR [archivo]")
    print("  - RENOMBRAR [viejo] [nuevo]")
    print("  - VERIFICAR [archivo]")
    if permisos == "admin":
        print("  - APROBAR_PERMISOS [id] [aprobar/rechazar]")
    print("  - SALIR")
