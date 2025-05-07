import socket
import ssl
import os
import sys
import logging
import subprocess
import hashlib

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.comandos import manejar_comando
from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario

def calcular_hash_archivo(ruta_archivo):
    """
    Calcula el hash SHA-256 de un archivo.

    Args:
        ruta_archivo (str): Ruta al archivo

    Returns:
        str: Hash SHA-256 en formato hexadecimal o None si hay un error
    """
    try:
        with open(ruta_archivo, 'rb') as f:
            contenido = f.read()
            return hashlib.sha256(contenido).hexdigest()
    except Exception as e:
        print(f"❌ Error al calcular hash: {e}")
        return None

DIRECTORIO_BASE = "servidorArchivos"

def iniciar_cliente(host, port):
    """
    Inicia el cliente para conectarse al servidor de archivos.

    Args:
        host (str): Dirección IP o nombre del host del servidor
        port (int): Puerto del servidor
    """
    try:
        # Crear contexto SSL
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE  # Para desarrollo, en producción usar CERT_REQUIRED

        # Conectar al servidor
        with socket.create_connection((host, port)) as sock:
            with contexto.wrap_socket(sock, server_hostname=host) as conexion_ssl:
                # Recibir mensaje de bienvenida
                mensaje_bienvenida = conexion_ssl.recv(1024).decode('utf-8')
                print(mensaje_bienvenida)

                while True:
                    # Recibir opciones del servidor
                    opciones = conexion_ssl.recv(1024).decode('utf-8')
                    print(opciones)

                    # Mostrar menú de opciones en caso de que no se reciba del servidor o no contenga las opciones
                    if not opciones.strip() or "Opciones:" not in opciones:
                        print("\n🔹 Opciones:\n   [1] Iniciar sesión\n   [2] Registrarse\n   [3] Salir\n\n👉 Selecciona una opción (1/2/3): ")

                    # Enviar opción seleccionada
                    opcion = input()
                    conexion_ssl.sendall(f"{opcion}\n".encode('utf-8'))

                    if opcion == '1':  # Iniciar sesión
                        # Recibir solicitud de usuario
                        solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')
                        print(solicitud_usuario)

                        # Enviar usuario
                        usuario = input()
                        conexion_ssl.sendall(f"{usuario}\n".encode('utf-8'))

                        # Recibir solicitud de contraseña
                        solicitud_password = conexion_ssl.recv(1024).decode('utf-8')
                        print(solicitud_password)

                        # Enviar contraseña
                        password = input()
                        conexion_ssl.sendall(f"{password}\n".encode('utf-8'))

                        # Recibir respuesta de autenticación
                        respuesta_auth = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta_auth)

                        if "✅ Autenticación exitosa" in respuesta_auth:
                            print("\n💻 Modo de comandos activado. Escribe 'SALIR' para desconectar.")
                            break  # Continuar al modo de comandos

                    elif opcion == '2':  # Registrarse
                        print("\n👤 Nuevo usuario: ")
                        nuevo_usuario = input()
                        print("🔒 Nueva contraseña: ")
                        nueva_password = input()

                        # Enviar comando de registro al servidor
                        conexion_ssl.sendall(f"REGISTRAR {nuevo_usuario} {nueva_password}\n".encode('utf-8'))

                        # Recibir respuesta de registro
                        respuesta_registro = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta_registro)

                        if "✅ Usuario registrado" in respuesta_registro:
                            # Recibir mensaje adicional del servidor
                            mensaje_adicional = conexion_ssl.recv(1024).decode('utf-8')
                            print(mensaje_adicional)

                            # Continuar con el flujo de inicio de sesión
                            print("\n👤 Usuario: ")
                            usuario = nuevo_usuario
                            print(usuario)
                            conexion_ssl.sendall(f"{usuario}\n".encode('utf-8'))

                            # Recibir solicitud de contraseña
                            solicitud_password = conexion_ssl.recv(1024).decode('utf-8')
                            print(solicitud_password)

                            # Enviar contraseña
                            password = nueva_password
                            print(password)
                            conexion_ssl.sendall(f"{password}\n".encode('utf-8'))

                            # Recibir respuesta de autenticación
                            respuesta_auth = conexion_ssl.recv(1024).decode('utf-8')
                            print(respuesta_auth)

                            if "✅ Autenticación exitosa" in respuesta_auth:
                                print("\n💻 Modo de comandos activado. Escribe 'SALIR' para desconectar.")
                                break  # Continuar al modo de comandos

                    elif opcion == '3':  # Salir
                        print("🔌 Desconectando...")
                        return

                # Modo de comandos
                while True:
                    # Recibir solicitud de comando
                    solicitud_comando = conexion_ssl.recv(1024).decode('utf-8')
                    print(solicitud_comando)

                    # Enviar comando
                    comando = input()

                    # Manejar comando CREAR especialmente para calcular y enviar hash
                    if comando.upper().startswith("CREAR "):
                        partes = comando.split()
                        if len(partes) == 2:
                            # Solicitar ruta del archivo local
                            print("📂 Ruta del archivo local: ")
                            archivo_local = input()

                            if os.path.exists(archivo_local):
                                # Calcular hash del archivo
                                hash_archivo = calcular_hash_archivo(archivo_local)

                                if hash_archivo:
                                    # Modificar comando para incluir el hash
                                    comando = f"{partes[0]} {partes[1]} {hash_archivo}"
                                    print(f"📤 Enviando comando con hash: {comando}")

                                    # Leer contenido del archivo para enviarlo al servidor
                                    try:
                                        with open(archivo_local, 'r') as f:
                                            contenido = f.read()
                                            # Aquí se podría implementar la transferencia del contenido
                                            # Por ahora solo enviamos el comando con el hash
                                    except Exception as e:
                                        print(f"❌ Error al leer archivo: {e}")
                                else:
                                    print("❌ No se pudo calcular el hash del archivo.")
                            else:
                                print(f"❌ El archivo local '{archivo_local}' no existe.")

                    conexion_ssl.sendall(f"{comando}\n".encode('utf-8'))

                    if comando.upper() == "SALIR":
                        print("🔌 Desconectando...")
                        break

                    # Recibir respuesta del comando
                    respuesta_comando = conexion_ssl.recv(1024).decode('utf-8')
                    print(respuesta_comando)

    except ConnectionRefusedError:
        print(f"❌ No se pudo conectar al servidor {host}:{port}. Asegúrate de que el servidor esté en ejecución.")
    except ssl.SSLError as e:
        print(f"❌ Error SSL: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

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


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("🌍 Iniciando cliente de archivos seguro...")

    # Obtener host y puerto del servidor
    host = 'localhost'
    port = 5050

    print("🌍 Cliente de Archivos Seguro")
    print("============================")
    print("Este cliente te permite conectarte a un servidor de archivos seguro.")
    print("Podrás registrarte, iniciar sesión y gestionar archivos de forma segura.")
    print(f"🌍 Conectando al Servidor de Archivos Seguro en {host}:{port}...")
    iniciar_cliente(host, port)
