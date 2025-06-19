
import os
import sys
import logging
from dotenv import load_dotenv

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from cli.ui.interface import mostrar_banner
from .seguridad_ssl import verificar_certificado_servidor, establecer_conexion_ssl
from .autenticacion import manejar_autenticacion
from .procesador_comandos import procesar_comandos

def iniciar_cliente(host, port):
    logger.info(f"🌐 Iniciando cliente para conectar a {host}:{port}")

    # Verificar el certificado del servidor antes de conectar
    cert_valido, cert_mensaje = verificar_certificado_servidor()

    # Mostrar información sobre el certificado
    if cert_valido:
        print(f"✅ {cert_mensaje}")
    else:
        print(f"⚠️ {cert_mensaje}")
        # Continuar automáticamente sin verificar el certificado
        logger.warning("Continuando sin verificar el certificado del servidor.")

    # Mostrar banner de bienvenida
    mostrar_banner()

    try:
        # Establecer conexión SSL con el servidor
        conexion_ssl = establecer_conexion_ssl(host, port, verificar_cert=cert_valido)
        if not conexion_ssl:
            # Mostrar mensaje adicional para ayudar al usuario
            from cli.ui.estilos import ANSI_AMARILLO, ANSI_RESET
            print(f"\n{ANSI_AMARILLO}ℹ️ Para iniciar el servidor, ejecuta:{ANSI_RESET}")
            print(f"{ANSI_AMARILLO}   python main.py -m server{ANSI_RESET}")
            print(f"{ANSI_AMARILLO}   o{ANSI_RESET}")
            print(f"{ANSI_AMARILLO}   python /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/main.py -m server{ANSI_RESET}\n")
            return

        # Manejar autenticación del usuario
        if not manejar_autenticacion(conexion_ssl):
            return

        # Procesar comandos del usuario
        procesar_comandos(conexion_ssl)

    except Exception as error:
        logger.error(f"❌ Error en el cliente: {error}")
        from cli.ui.estilos import ANSI_ROJO, ANSI_RESET
        print(f"{ANSI_ROJO}❌ Error: {error}{ANSI_RESET}")
