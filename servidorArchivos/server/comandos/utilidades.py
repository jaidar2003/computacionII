"""
Utilidades compartidas para el sistema de comandos.

Este módulo contiene funciones de utilidad que son compartidas
entre diferentes módulos del sistema de comandos.
"""

import socket

def _enviar_mensaje(conexion, mensaje):
    """
    Envía un mensaje a través de la conexión especificada.
    
    Args:
        conexion (socket): Conexión socket para enviar el mensaje
        mensaje (str): Mensaje a enviar
    """
    if conexion:
        conexion.sendall(mensaje.encode('utf-8'))