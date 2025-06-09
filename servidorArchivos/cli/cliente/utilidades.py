"""
Módulo de utilidades para el cliente.

Este módulo contiene funciones auxiliares utilizadas por los diferentes
componentes del cliente del servidor de archivos.
"""

import os
import sys
import logging

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
logger = logging.getLogger(__name__)

def enviar_mensaje(conexion, mensaje):
    """
    Envía un mensaje al servidor.
    
    Args:
        conexion (socket): Conexión SSL con el servidor
        mensaje (str): Mensaje a enviar
    """
    conexion.sendall(mensaje.encode('utf-8'))

def enviar_comando(conexion, comando):
    """
    Envía un comando al servidor.
    
    Args:
        conexion (socket): Conexión SSL con el servidor
        comando (str): Comando a enviar
    """
    enviar_mensaje(conexion, comando)