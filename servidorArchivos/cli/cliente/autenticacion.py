"""
Módulo de autenticación para el cliente.

Este módulo contiene las funciones relacionadas con la autenticación
de usuarios en el servidor de archivos.
"""

import os
import sys
import logging

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from cli.interface import mostrar_menu_principal, mostrar_comandos_disponibles
from cli.utils import input_password
from cli.estilos import ANSI_VERDE, ANSI_RESET, ANSI_ROJO
from cli.mensajes import ERROR_CREDENCIALES_INVALIDAS, MENSAJE_DESCONECTAR
from .utilidades import enviar_mensaje, enviar_comando

# Constantes
BUFFER_SIZE = 1024  # Tamaño del buffer para recibir datos

def recibir_mensajes_bienvenida(conexion):
    """
    Recibe y muestra mensajes de bienvenida del servidor.
    
    Args:
        conexion (socket): Conexión SSL con el servidor
    """
    mensaje = conexion.recv(BUFFER_SIZE).decode('utf-8')
    print(ANSI_VERDE + mensaje + ANSI_RESET)

def manejar_autenticacion(conexion):
    """
    Maneja autenticación o registro. 
    
    Args:
        conexion (socket): Conexión SSL con el servidor
        
    Returns:
        bool: True si exitoso, False en caso contrario
    """
    # Recibir mensajes de bienvenida
    recibir_mensajes_bienvenida(conexion)
    
    while True:
        mostrar_menu_principal()
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            # Iniciar sesión
            if iniciar_sesion(conexion):
                return True

        elif opcion == '2':
            # Registrar nuevo usuario
            registrar_usuario(conexion)

        elif opcion == '3':
            # Salir
            enviar_comando(conexion, "SALIR")
            print(MENSAJE_DESCONECTAR)
            return False

        else:
            print(f"❌ Opción no válida: {opcion}")

def iniciar_sesion(conexion):
    """
    Inicia sesión en el servidor.
    
    Args:
        conexion (socket): Conexión SSL con el servidor
        
    Returns:
        bool: True si exitoso, False en caso contrario
    """
    conexion.recv(BUFFER_SIZE)  # Descartar el prompt "Usuario: " del servidor

    # Solicitar credenciales
    usuario = input("Usuario: ")
    enviar_mensaje(conexion, f"{usuario}")
    conexion.recv(BUFFER_SIZE)  # Recibir prompt de contraseña

    password = input_password("Contraseña: ")
    enviar_mensaje(conexion, f"{password}")

    # Verificar respuesta
    respuesta_auth = conexion.recv(BUFFER_SIZE).decode('utf-8')
    if "✅ Autenticación exitosa" in respuesta_auth:
        print(ANSI_VERDE + respuesta_auth + ANSI_RESET)
        mostrar_comandos_disponibles("lectura")
        return True
    else:
        print(ANSI_ROJO + ERROR_CREDENCIALES_INVALIDAS + ANSI_RESET)
        return False

def registrar_usuario(conexion):
    """
    Registra un nuevo usuario en el servidor.
    
    Args:
        conexion (socket): Conexión SSL con el servidor
    """
    nuevo_usuario = input("Nuevo usuario: ")
    nueva_password = input_password("Nueva contraseña: ")

    enviar_comando(conexion, f"REGISTRAR {nuevo_usuario} {nueva_password}")
    respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')

    if "✅" in respuesta:
        print(ANSI_VERDE + respuesta + ANSI_RESET)
        print(ANSI_VERDE + "👤 Por favor, inicie sesión con sus nuevas credenciales." + ANSI_RESET)
    else:
        print(ANSI_ROJO + respuesta + ANSI_RESET)