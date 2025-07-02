import socket

def _enviar_mensaje(conexion, mensaje):
    if conexion:
        conexion.sendall(mensaje.encode('utf-8'))