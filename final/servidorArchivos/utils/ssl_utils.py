import os
import sys
import ssl
import socket
import logging
import errno
from dotenv import load_dotenv

# Configuración básica
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# ANSI color codes (previously imported from cli.ui.estilos)
ANSI_VERDE = "\033[92m"
ANSI_RESET = "\033[0m"
ANSI_ROJO = "\033[91m"
ANSI_AMARILLO = "\033[93m"

def es_direccion_ip(host):
    """Verifica si el host es una dirección IP (IPv4 o IPv6)."""
    try:
        # Intentar interpretar como IPv4
        socket.inet_pton(socket.AF_INET, host)
        return True
    except socket.error:
        try:
            # Intentar interpretar como IPv6
            socket.inet_pton(socket.AF_INET6, host)
            return True
        except socket.error:
            # No es una dirección IP válida
            return False

def establecer_conexion_ssl(host, port, verificar_cert=True):
    # Configurar contexto SSL con verificación de certificado
    contexto = ssl.create_default_context()

    # Configurar verificación según el parámetro
    if verificar_cert:
        # Habilitar verificación de certificado
        contexto.verify_mode = ssl.CERT_REQUIRED

        # Habilitar verificación de hostname solo si estamos usando un nombre de dominio
        if es_direccion_ip(host):
            # Es una dirección IP (IPv4 o IPv6), desactivar verificación de hostname
            contexto.check_hostname = False
            logger.info(f"Desactivando verificación de hostname para dirección IP: {host}")
        else:
            # Es un nombre de dominio, activar verificación de hostname
            contexto.check_hostname = True
            logger.info(f"Activando verificación de hostname para nombre de dominio: {host}")

        # Cargar el certificado del servidor como certificado de confianza
        cert_path = os.getenv("CERT_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "certificados", "certificado.pem"))

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
            print(f"{ANSI_ROJO}❌ Asegúrate de que el servidor esté en ejecución.{ANSI_RESET}")
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