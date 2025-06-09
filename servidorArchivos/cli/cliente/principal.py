"""
Módulo principal del cliente para el servidor de archivos.

Este módulo contiene la función principal que inicia el cliente y coordina
todas las operaciones con el servidor de archivos.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from cli.interface import mostrar_banner
from .seguridad_ssl import verificar_certificado_servidor, establecer_conexion_ssl
from .autenticacion import manejar_autenticacion
from .procesador_comandos import procesar_comandos

def iniciar_cliente(host, port):
    """
    Inicia el cliente y conecta al servidor en host:port.
    
    Args:
        host (str): Dirección del servidor
        port (int): Puerto del servidor
        
    Returns:
        None
    """
    logger.info(f"🌐 Iniciando cliente para conectar a {host}:{port}")

    # Verificar el certificado del servidor antes de conectar
    cert_valido, cert_mensaje = verificar_certificado_servidor()

    # Mostrar información sobre el certificado
    if cert_valido:
        print(f"✅ {cert_mensaje}")
    else:
        print(f"⚠️ {cert_mensaje}")
        continuar = input("⚠️ ¿Desea continuar sin verificar el certificado? (s/n): ")
        if continuar.lower() != 's':
            print("🛑 Conexión cancelada por el usuario.")
            return

    # Mostrar banner de bienvenida
    mostrar_banner()

    try:
        # Establecer conexión SSL con el servidor
        conexion_ssl = establecer_conexion_ssl(host, port, verificar_cert=cert_valido)
        if not conexion_ssl:
            return

        # Manejar autenticación del usuario
        if not manejar_autenticacion(conexion_ssl):
            return

        # Procesar comandos del usuario
        procesar_comandos(conexion_ssl)

    except Exception as error:
        logger.error(f"❌ Error en el cliente: {error}")
        print(f"❌ Error: {error}")