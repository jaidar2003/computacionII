# cli/ui/interface.py

from .estilos import ANSI_AMARILLO, ANSI_AZUL, ANSI_RESET

# Constante adicional para el color cian usado en los bordes
ANSI_CIAN = "\033[1;36m"

# Caracteres Unicode para los bordes
BORDE_SUPERIOR_IZQ = "\u2554"
BORDE_SUPERIOR_DER = "\u2557"
BORDE_INFERIOR_IZQ = "\u255A"
BORDE_INFERIOR_DER = "\u255D"
BORDE_HORIZONTAL = "\u2550"
BORDE_VERTICAL = "\u2551"

def mostrar_banner():
    # Ancho total del banner
    ancho = 50
    # Texto a centrar
    texto = "CLIENTE DE ARCHIVOS SEGURO"
    # Calcular espacios para centrar correctamente
    espacios = (ancho - len(texto)) // 2
    texto_centrado = " " * espacios + texto + " " * (ancho - len(texto) - espacios)

    print(f"\n{ANSI_CIAN}{BORDE_SUPERIOR_IZQ}{BORDE_HORIZONTAL * ancho}{BORDE_SUPERIOR_DER}{ANSI_RESET}")
    print(f"{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}{ANSI_AMARILLO}{texto_centrado}{ANSI_RESET}{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}")
    print(f"{ANSI_CIAN}{BORDE_INFERIOR_IZQ}{BORDE_HORIZONTAL * ancho}{BORDE_INFERIOR_DER}{ANSI_RESET}\n")

def mostrar_menu_principal():
    # Ancho total del menú
    ancho = 40

    print(f"\n{ANSI_CIAN}{BORDE_SUPERIOR_IZQ}{BORDE_HORIZONTAL * ancho}{BORDE_SUPERIOR_DER}{ANSI_RESET}")

    # Texto "Opciones:" centrado
    texto = "Opciones:"
    espacios = (ancho - len(texto)) // 2
    texto_centrado = " " * espacios + texto + " " * (ancho - len(texto) - espacios)
    print(f"{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}{ANSI_AMARILLO}{texto_centrado}{ANSI_RESET}{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}")

    # Opciones del menú
    opcion1 = "  [1] Iniciar sesión"
    opcion2 = "  [2] Registrarse"
    opcion3 = "  [3] Salir"
    print(f"{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}{opcion1}{' ' * (ancho - len(opcion1))}{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}")
    print(f"{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}{opcion2}{' ' * (ancho - len(opcion2))}{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}")
    print(f"{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}{opcion3}{' ' * (ancho - len(opcion3))}{ANSI_CIAN}{BORDE_VERTICAL}{ANSI_RESET}")

    print(f"{ANSI_CIAN}{BORDE_INFERIOR_IZQ}{BORDE_HORIZONTAL * ancho}{BORDE_INFERIOR_DER}{ANSI_RESET}")

def mostrar_comandos_disponibles(permisos):
    print(f"\n{ANSI_AZUL}Comandos disponibles:{ANSI_RESET}")
    print("  - LISTAR")
    print("  - SUBIR [ruta_archivo]")
    print("  - DESCARGAR [archivo]")
    print("  - ELIMINAR [archivo]")
    print("  - RENOMBRAR [viejo] [nuevo]")
    print("  - VERIFICAR [archivo]")
    if permisos == "admin":
        print("  - APROBAR_PERMISOS [id] [aprobar/rechazar]")
        print("  - LISTAR_USUARIOS")
    print("  - SALIR")
