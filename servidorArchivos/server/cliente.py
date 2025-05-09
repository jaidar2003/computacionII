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

def iniciar_cliente(host, port, test_mode=False):
    """
    Inicia el cliente para conectarse al servidor de archivos.

    Args:
        host (str): Dirección IP o nombre del host del servidor
        port (int): Puerto del servidor
        test_mode (bool): Indica si se está ejecutando en modo de prueba
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

                # Recibir solicitud de usuario
                solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')
                print(solicitud_usuario)

                # Bandera para controlar el flujo de autenticación
                autenticado = False

                # Bucle de autenticación
                while not autenticado:
                    # Mostrar menú de opciones localmente
                    opcion = input("\n🔹 Opciones:\n   [1] Iniciar sesión\n   [2] Registrarse\n   [3] Salir\n 👉 Selecciona una opción (1/2/3): ")

                    if opcion == '1':  # Iniciar sesión
                        # Enviar nombre de usuario
                        usuario = input("\n👤 Usuario: ")
                        conexion_ssl.sendall(f"{usuario}\n".encode('utf-8'))

                        # Recibir solicitud de contraseña
                        solicitud_password = conexion_ssl.recv(1024).decode('utf-8')

                        # Enviar contraseña
                        password = input(solicitud_password)
                        conexion_ssl.sendall(f"{password}\n".encode('utf-8'))

                        # Recibir respuesta de autenticación
                        respuesta_auth = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta_auth)

                        if "✅ Autenticación exitosa" in respuesta_auth:
                            print("\n💻 Modo de comandos activado")
                            print("\n📋 Comandos disponibles:")
                            print("  • LISTAR - Muestra todos los archivos en el servidor")
                            print("  • CREAR [nombre_archivo] - Crea un nuevo archivo")
                            print("  • ELIMINAR [nombre_archivo] - Elimina un archivo")
                            print("  • RENOMBRAR [nombre_viejo] [nombre_nuevo] - Renombra un archivo")
                            print("  • SALIR - Desconecta del servidor")
                            autenticado = True
                            break  # Salir del bucle de autenticación
                        else:
                            # Si la autenticación falló, mostrar opciones claras
                            try:
                                print("\n❌ Credenciales inválidas. ¿Qué deseas hacer?")
                                siguiente_opcion = input("1. Intentar nuevamente\n2. Salir\n👉 Selecciona una opción (1/2): ")
                                if siguiente_opcion == "2" or siguiente_opcion.upper() == "SALIR":
                                    conexion_ssl.sendall("SALIR\n".encode('utf-8'))
                                    print("🔌 Desconectando...")
                                    return
                            except:
                                pass

                            # Si eligió intentar nuevamente, volver a recibir la solicitud de usuario
                            solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')
                            print(solicitud_usuario)
                            continue

                    elif opcion == '2':  # Registrarse
                        # Solicitar datos para registro
                        nuevo_usuario = input("\n👤 Nuevo usuario: ")
                        nueva_password = input("🔒 Nueva contraseña: ")

                        # Enviar comando de registro
                        conexion_ssl.sendall(f"REGISTRAR {nuevo_usuario} {nueva_password}\n".encode('utf-8'))

                        # Recibir respuesta de registro
                        respuesta_registro = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta_registro)

                        if "✅ Usuario registrado" in respuesta_registro:
                            # Preguntar al usuario si desea iniciar sesión
                            try:
                                siguiente_opcion = input("\n¿Desea iniciar sesión con el usuario recién registrado?\n1. Sí, iniciar sesión\n2. No, volver al menú principal\n3. Salir\n")
                                if siguiente_opcion == "3":
                                    conexion_ssl.sendall("SALIR\n".encode('utf-8'))
                                    print("🔌 Desconectando...")
                                    return
                                elif siguiente_opcion == "2":
                                    # Enviar SALIR para terminar la sesión actual
                                    conexion_ssl.sendall("SALIR\n".encode('utf-8'))
                                    print("🔄 Volviendo al menú principal...")

                                    # Recibir nueva solicitud de usuario
                                    solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')
                                    print(solicitud_usuario)
                                    continue
                            except:
                                pass

                            # Si eligió iniciar sesión o hubo un error, continuar con el flujo normal
                            # Recibir mensaje adicional del servidor
                            mensaje_adicional = conexion_ssl.recv(1024).decode('utf-8')
                            print(mensaje_adicional)

                            # Recibir nueva solicitud de usuario para iniciar sesión
                            solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')

                            # Enviar el usuario recién registrado
                            conexion_ssl.sendall(f"{nuevo_usuario}\n".encode('utf-8'))

                            # Recibir solicitud de contraseña
                            solicitud_password = conexion_ssl.recv(1024).decode('utf-8')

                            # Enviar la contraseña recién registrada
                            conexion_ssl.sendall(f"{nueva_password}\n".encode('utf-8'))

                            # Recibir respuesta de autenticación
                            respuesta_auth = conexion_ssl.recv(1024).decode('utf-8')
                            print(respuesta_auth)

                            if "✅ Autenticación exitosa" in respuesta_auth:
                                print("\n💻 Modo de comandos activado. Escribe 'SALIR' para desconectar.")
                                print("\n📋 Comandos disponibles:")
                                print("  • LISTAR - Muestra todos los archivos en el servidor")
                                print("  • CREAR [nombre_archivo] - Crea un nuevo archivo")
                                print("  • ELIMINAR [nombre_archivo] - Elimina un archivo")
                                print("  • RENOMBRAR [nombre_viejo] [nombre_nuevo] - Renombra un archivo")
                                print("  • SALIR - Desconecta del servidor")
                                autenticado = True

                                # No procesamos comandos adicionales aquí, dejamos que el bucle principal de comandos lo haga

                                break  # Salir del bucle de autenticación

                        # Recibir nueva solicitud de usuario
                        solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')
                        print(solicitud_usuario)
                        continue

                    elif opcion == '3':  # Salir
                        # Enviar comando SALIR para salir
                        conexion_ssl.sendall("SALIR\n".encode('utf-8'))
                        print("🔌 Desconectando...")
                        return

                    else:
                        print("❌ Opción inválida. Intenta nuevamente.")
                        # Recibir nueva solicitud de usuario
                        solicitud_usuario = conexion_ssl.recv(1024).decode('utf-8')
                        print(solicitud_usuario)
                        continue

                # Modo de comandos
                while True:
                    try:
                        # Recibir solicitud de comando
                        solicitud_comando = conexion_ssl.recv(1024).decode('utf-8')

                        # Enviar comando
                        comando = input(solicitud_comando)
                    except Exception as e:
                        print(f"❌ Error al recibir comando: {e}")
                        break

                    # Manejar comando CREAR especialmente para calcular y enviar hash
                    if comando.upper().startswith("CREAR "):
                        partes = comando.split()
                        if len(partes) == 2:
                            # Solicitar ruta del archivo local
                            archivo_local = input("📂 Ruta del archivo local: ")

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

                    try:
                        # Enviar el comando actual
                        conexion_ssl.sendall(f"{comando}\n".encode('utf-8'))

                        # Si el comando es SALIR, terminar
                        if comando.upper() == "SALIR":
                            print("🔌 Desconectando...")
                            break
                        else:
                            # Recibir respuesta del comando
                            respuesta_comando = conexion_ssl.recv(1024).decode('utf-8')
                            print(respuesta_comando)
                    except Exception as e:
                        print(f"❌ Error al enviar comando o recibir respuesta: {e}")
                        break

    except ConnectionRefusedError:
        print(f"❌ No se pudo conectar al servidor {host}:{port}. Asegúrate de que el servidor esté en ejecución.")
    except ssl.SSLError as e:
        print(f"❌ Error SSL: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")



if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("🌍 Iniciando cliente de archivos seguro...")

    # Obtener host y puerto del servidor
    host = 'localhost'
    port = 5050

    # Imprimir un banner más atractivo
    print("\n" + "="*60)
    print("🌟 🔒 🌟 CLIENTE DE ARCHIVOS SEGURO 🌟 🔒 🌟".center(60))
    print("="*60)
    print("\n📋 INFORMACIÓN:")
    print("  • Este cliente te permite conectarte a un servidor de archivos seguro")
    print("  • Podrás registrarte, iniciar sesión y gestionar archivos de forma segura")
    print("  • Todas las comunicaciones están protegidas con encriptación SSL")
    print("\n🔄 ESTADO:")
    print(f"  • Conectando al Servidor de Archivos Seguro en {host}:{port}...")
    print("="*60 + "\n")
    iniciar_cliente(host, port)
