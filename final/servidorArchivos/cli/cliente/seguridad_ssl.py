import os
import sys
import ssl
import socket
import datetime
import logging
import errno

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from cli.ui.estilos import ANSI_VERDE, ANSI_RESET, ANSI_ROJO, ANSI_AMARILLO

# Constantes
DIAS_AVISO_EXPIRACION = 30  # Días antes de expiración para mostrar advertencia

def verificar_certificado_servidor():

    cert_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                           "certificados", "certificado.pem")

    if not os.path.exists(cert_path):
        return False, f"No se encontró el certificado del servidor en {cert_path}"

    try:
        # Leer el contenido del certificado
        with open(cert_path, 'r') as f:
            cert_data = f.read()

        # Crear un contexto SSL temporal para analizar el certificado
        context = ssl.create_default_context()
        context.load_verify_locations(cadata=cert_data)

        # Obtener información del certificado
        cert = ssl._ssl._test_decode_cert(cert_path)

        # Extraer fecha de expiración
        not_after = cert.get('notAfter', '')
        if not not_after:
            return False, "No se pudo determinar la fecha de expiración del certificado"

        # Formato de fecha en certificados: 'May 30 00:00:00 2023 GMT'
        try:
            expiracion = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            hoy = datetime.datetime.now()

            # Verificar si ya expiró
            if hoy > expiracion:
                return False, f"El certificado del servidor ha expirado el {not_after}"

            # Verificar si está por expirar
            dias_restantes = (expiracion - hoy).days
            if dias_restantes <= DIAS_AVISO_EXPIRACION:
                return True, f"El certificado del servidor expirará en {dias_restantes} días ({not_after})"

            # Certificado válido
            return True, f"Certificado del servidor válido hasta {not_after}"

        except ValueError as e:
            return False, f"Error al analizar la fecha de expiración del certificado: {e}"

    except Exception as e:
        return False, f"Error al verificar el certificado del servidor: {e}"

def establecer_conexion_ssl(host, port, verificar_cert=True):
    # Configurar contexto SSL con verificación de certificado
    contexto = ssl.create_default_context()

    # Configurar verificación según el parámetro
    if verificar_cert:
        # Habilitar verificación de certificado
        contexto.verify_mode = ssl.CERT_REQUIRED

        # Habilitar verificación de hostname si estamos usando un nombre de dominio
        if not host.replace('.', '').isdigit():  # Si no es una IP
            contexto.check_hostname = True
        else:
            contexto.check_hostname = False

        # Cargar el certificado del servidor como certificado de confianza
        cert_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "certificados", "certificado.pem")

        if os.path.exists(cert_path):
            contexto.load_verify_locations(cafile=cert_path)
            logger.info("Certificado del servidor cargado correctamente.")
        else:
            logger.warning(f"No se encontró el certificado del servidor en {cert_path}")
            logger.warning("La conexión no será segura sin verificación de certificado.")
            # Fallback a modo sin verificación si no encontramos el certificado
            contexto.check_hostname = False
            contexto.verify_mode = ssl.CERT_NONE
    else:
        # Deshabilitar verificación de certificado
        logger.warning("Verificación de certificado deshabilitada.")
        # No mostrar advertencia al usuario para evitar confusión
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE

    try:
        # Establecer conexión
        sock = socket.create_connection((host, port))
        # Configurar timeout para operaciones de socket (120 segundos)
        sock.settimeout(120)
        conexion_ssl = contexto.wrap_socket(sock, server_hostname=host)

        # Verificar y mostrar información del certificado
        cert = conexion_ssl.getpeercert()
        if cert:
            subject = dict(x[0] for x in cert['subject'])
            issuer = dict(x[0] for x in cert['issuer'])
            print(f"🔒 Conectado a servidor con certificado:")
            print(f"   - Emitido para: {subject.get('commonName', 'Desconocido')}")
            print(f"   - Emitido por: {issuer.get('commonName', 'Desconocido')}")
            print(f"   - Válido hasta: {cert.get('notAfter', 'Desconocido')}")

        logger.debug(f"🔌 Conexión segura establecida con {host}:{port}")
        return conexion_ssl

    except socket.error as e:
        # Manejar específicamente el error de conexión rechazada
        if hasattr(e, 'errno') and e.errno == errno.ECONNREFUSED:
            print(f"{ANSI_ROJO}❌ Error al establecer conexión: Conexión rechazada{ANSI_RESET}")
            print(f"{ANSI_ROJO}❌ El servidor no está en ejecución o no es accesible en {host}:{port}{ANSI_RESET}")
            print(f"{ANSI_ROJO}❌ Asegúrate de que el servidor esté en ejecución antes de iniciar el cliente.{ANSI_RESET}")
            logger.error(f"Conexión rechazada al intentar conectar a {host}:{port}. El servidor no está en ejecución.")
        else:
            print(f"{ANSI_ROJO}❌ Error de red al establecer conexión: {e}{ANSI_RESET}")
            logger.error(f"Error de socket al conectar a {host}:{port}: {e}")
        return None
    except ssl.SSLError as e:
        print(f"{ANSI_ROJO}❌ Error de verificación SSL: {e}{ANSI_RESET}")
        print(f"{ANSI_ROJO}❌ No se pudo verificar la identidad del servidor.{ANSI_RESET}")
        print(f"{ANSI_ROJO}❌ Esto podría indicar un intento de ataque 'man-in-the-middle'.{ANSI_RESET}")
        logger.error(f"Error SSL al conectar a {host}:{port}: {e}")
        return None
    except Exception as e:
        print(f"{ANSI_ROJO}❌ Error al establecer conexión: {e}{ANSI_RESET}")
        logger.error(f"Error general al conectar a {host}:{port}: {e}")
        return None
