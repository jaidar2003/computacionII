# cli/cliente.py

import socket
import ssl
import sys
import os
import logging
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Cargar variables de entorno
load_dotenv()

from server.comandos import manejar_comando
from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario
from cli.utils import input_password, calcular_hash_archivo
from cli.interface import mostrar_banner, mostrar_menu_principal, mostrar_comandos_disponibles
from cli.mensajes import ERROR_CREDENCIALES_INVALIDAS, MENSAJE_DESCONECTAR, MENSAJE_ENVIO_HASH
from cli.estilos import ANSI_VERDE, ANSI_RESET, ANSI_ROJO

# Usar variable de entorno o valor por defecto
DIRECTORIO_BASE = os.getenv("CLIENTE_DIR", "servidorArchivos")

def iniciar_cliente(host, port):
    try:
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE

        with socket.create_connection((host, port)) as sock:
            with contexto.wrap_socket(sock, server_hostname=host) as conexion_ssl:
                print(ANSI_VERDE + conexion_ssl.recv(1024).decode('utf-8') + ANSI_RESET)
                print(ANSI_VERDE + conexion_ssl.recv(1024).decode('utf-8') + ANSI_RESET)

                autenticado = False
                while not autenticado:
                    mostrar_menu_principal()
                    opcion = input("Seleccione una opción: ")

                    if opcion == '1':
                        usuario = input("Usuario: ")
                        conexion_ssl.sendall(f"{usuario}\n".encode('utf-8'))
                        conexion_ssl.recv(1024)
                        password = input_password("Contraseña: ")
                        conexion_ssl.sendall(f"{password}\n".encode('utf-8'))
                        respuesta_auth = conexion_ssl.recv(1024).decode('utf-8')
                        if "✅ Autenticación exitosa" in respuesta_auth:
                            print(ANSI_VERDE + respuesta_auth + ANSI_RESET)
                            mostrar_comandos_disponibles("lectura")
                            autenticado = True
                        else:
                            print(ANSI_ROJO + ERROR_CREDENCIALES_INVALIDAS + ANSI_RESET)

                    elif opcion == '2':
                        nuevo_usuario = input("Nuevo usuario: ")
                        nueva_password = input_password("Nueva contraseña: ")
                        conexion_ssl.sendall(f"REGISTRAR {nuevo_usuario} {nueva_password}\n".encode('utf-8'))
                        print(conexion_ssl.recv(1024).decode('utf-8'))

                    elif opcion == '3':
                        conexion_ssl.sendall("SALIR\n".encode('utf-8'))
                        print(MENSAJE_DESCONECTAR)
                        return

                while True:
                    comando = input(conexion_ssl.recv(1024).decode('utf-8'))
                    if comando.upper().startswith("CREAR "):
                        partes = comando.split()
                        if len(partes) == 2:
                            archivo_local = input("Ruta al archivo local: ")
                            if os.path.exists(archivo_local):
                                hash_archivo = calcular_hash_archivo(archivo_local)
                                if hash_archivo:
                                    comando = f"{partes[0]} {partes[1]} {hash_archivo}"
                                    print(MENSAJE_ENVIO_HASH.format(comando=comando))
                    conexion_ssl.sendall(f"{comando}\n".encode('utf-8'))
                    if comando.upper() == "SALIR":
                        print(MENSAJE_DESCONECTAR)
                        break
                    print(conexion_ssl.recv(1024).decode('utf-8'))

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mostrar_banner()

    # Usar variables de entorno para host y puerto
    host = os.getenv("SERVIDOR_HOST", "127.0.0.0")
    port = int(os.getenv("SERVIDOR_PORT", 1608))

    # Si el host es 0.0.0.0 (escucha en todas las interfaces), conectar a localhost
    cliente_host = "localhost" if host == "0.0.0.0" else host

    iniciar_cliente(cliente_host, port)
