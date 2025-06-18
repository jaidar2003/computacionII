
import os
import sys
import logging

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
logger = logging.getLogger(__name__)

def enviar_mensaje(conexion, mensaje):
    conexion.sendall(mensaje.encode('utf-8'))

def enviar_comando(conexion, comando):
    enviar_mensaje(conexion, comando)
