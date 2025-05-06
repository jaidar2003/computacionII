import sys
import os
import socket
import ssl
import logging
import subprocess

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from comandos import manejar_comando
from seguridad import autenticar_usuario_en_servidor, registrar_usuario

DIRECTORIO_BASE = "servidorArchivos"

def iniciar_cliente(host, port, timeout=5):
    """
    Inicia un cliente que se conecta al servidor en la dirección y puerto especificados.

    Args:
        host (str): Dirección IP o nombre de host del servidor
        port (int): Puerto del servidor
        timeout (int): Tiempo máximo de espera para la conexión en segundos
    """
    try:
        # Crear contexto SSL
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE

        # Conectar al servidor con timeout
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with contexto.wrap_socket(sock, server_hostname=host) as conexion_ssl:
                # Recibir mensaje de bienvenida
                mensaje = conexion_ssl.recv(1024).decode('utf-8')
                print(mensaje)

                while True:
                    # Mostrar opciones
                    print("\n🔹 Opciones:")
                    print("   [1] Iniciar sesión")
                    print("   [2] Registrarse")
                    print("   [3] Salir")

                    opcion = input("\n👉 Selecciona una opción (1/2/3): ")

                    if opcion == '1':
                        # Iniciar sesión
                        usuario = input("\n👤 Usuario: ")
                        password = input("🔒 Contraseña: ")

                        # Enviar credenciales
                        conexion_ssl.sendall(f"{usuario}\n".encode())
                        conexion_ssl.sendall(f"{password}\n".encode())

                        # Recibir respuesta
                        respuesta = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta)

                        if "✅" in respuesta:
                            # Autenticación exitosa
                            while True:
                                comando = input("\n💻 Ingresar comando ('SALIR' para desconectar): ")
                                conexion_ssl.sendall(f"{comando}\n".encode())

                                if comando.upper() == "SALIR":
                                    break

                                # Recibir respuesta del comando
                                respuesta = conexion_ssl.recv(1024).decode('utf-8')
                                print(respuesta)

                            break

                    elif opcion == '2':
                        # Registrarse
                        nuevo_usuario = input("\n👤 Nuevo usuario: ")
                        nueva_contraseña = input("🔒 Nueva contraseña: ")

                        # Enviar comando de registro
                        conexion_ssl.sendall(f"REGISTRAR {nuevo_usuario} {nueva_contraseña}\n".encode())

                        # Recibir respuesta
                        respuesta = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta)

                    elif opcion == '3':
                        # Salir
                        break

                    else:
                        print("❌ Opción inválida.")

    except socket.error as e:
        print(f"\n❌ Error de conexión: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def manejar_cliente(conexion_ssl, direccion, directorio=DIRECTORIO_BASE):
    try:
        logging.info(f"🔗 Conexión aceptada desde {direccion}")
        conexion_ssl.sendall("🌍 Bienvenido al server de archivos seguro.\n".encode('utf-8'))

        autenticado = False
        usuario_id = None
        permisos = None

        while not autenticado:
            conexion_ssl.sendall("\n🔹 Opciones:\n   [1] Iniciar sesión\n   [2] Registrarse\n   [3] Salir\n\n👉 Selecciona una opción (1/2/3): ".encode('utf-8'))
            opcion = conexion_ssl.recv(1024).decode().strip()

            if opcion == '1':
                conexion_ssl.sendall("\n👤 Usuario: ".encode('utf-8'))
                usuario = conexion_ssl.recv(1024).decode().strip()
                conexion_ssl.sendall("🔒 Contraseña: ".encode('utf-8'))
                password = conexion_ssl.recv(1024).decode().strip()

                datos_usuario = autenticar_usuario_en_servidor(usuario, password)
                if not datos_usuario:
                    conexion_ssl.sendall("❌ Credenciales inválidas.\n".encode('utf-8'))
                    continue

                usuario_id, permisos = datos_usuario
                conexion_ssl.sendall(f"✅ Autenticación exitosa! Permisos: {permisos}\n".encode('utf-8'))
                autenticado = True

            elif opcion == '2':
                conexion_ssl.sendall("\n👤 Nuevo usuario: ".encode('utf-8'))
                nuevo_usuario = conexion_ssl.recv(1024).decode().strip()
                conexion_ssl.sendall("🔒 Nueva contraseña: ".encode('utf-8'))
                nueva_contraseña = conexion_ssl.recv(1024).decode().strip()

                respuesta = registrar_usuario(nuevo_usuario, nueva_contraseña)
                conexion_ssl.sendall(f"{respuesta}\n".encode('utf-8'))

                # Auto-login tras registro exitoso
                if "✅ Usuario registrado" in respuesta:
                    datos_usuario = autenticar_usuario_en_servidor(nuevo_usuario, nueva_contraseña)
                    if datos_usuario:
                        usuario_id, permisos = datos_usuario
                        conexion_ssl.sendall(f"✅ Autenticación automática exitosa! Permisos: {permisos}\n".encode('utf-8'))
                        autenticado = True

            elif opcion == '3':
                conexion_ssl.sendall("🔌 Desconectando...\n".encode('utf-8'))
                return
            else:
                conexion_ssl.sendall("❌ Opción inválida.\n".encode('utf-8'))

        while True:
            conexion_ssl.sendall("\n💻 Ingresar comando ('SALIR' para desconectar): ".encode('utf-8'))
            comando = conexion_ssl.recv(1024).decode().strip()
            logging.info(f"📥 Comando recibido: {comando}")

            if comando.upper() == "SALIR":
                conexion_ssl.sendall("🔌 Desconectando...\n".encode('utf-8'))
                break

            respuesta = manejar_comando(comando, directorio, usuario_id)
            conexion_ssl.sendall(f"📄 {respuesta}\n".encode('utf-8'))

    except Exception as e:
        logging.error(f"❌ Error con cliente {direccion}: {e}")
    finally:
        conexion_ssl.close()
        logging.info(f"🔌 Conexión cerrada con {direccion}")

# Ejecutar el cliente cuando se ejecuta este archivo directamente
if __name__ == "__main__":
    print("🌍 Iniciando Cliente de Archivos Seguro...")
    try:
        # Usar valores predeterminados para host y puerto
        host = '127.0.0.1'
        port = 5050
        print(f"🔌 Conectando al servidor en {host}:{port}")
        iniciar_cliente(host, port)
    except KeyboardInterrupt:
        print("\n🛑 Cliente detenido por el usuario")
