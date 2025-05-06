import socket
import ssl
import os
import logging
import subprocess
from comandos import manejar_comando
from seguridad import autenticar_usuario_en_servidor, registrar_usuario

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
                            break  # Continuar al modo de comandos

                    elif opcion == '2':  # Registrarse
                        # Recibir solicitud de nuevo usuario
                        solicitud_nuevo_usuario = conexion_ssl.recv(1024).decode('utf-8')
                        print(solicitud_nuevo_usuario)

                        # Enviar nuevo usuario
                        nuevo_usuario = input()
                        conexion_ssl.sendall(f"{nuevo_usuario}\n".encode('utf-8'))

                        # Recibir solicitud de nueva contraseña
                        solicitud_nueva_password = conexion_ssl.recv(1024).decode('utf-8')
                        print(solicitud_nueva_password)

                        # Enviar nueva contraseña
                        nueva_password = input()
                        conexion_ssl.sendall(f"{nueva_password}\n".encode('utf-8'))

                        # Recibir respuesta de registro
                        respuesta_registro = conexion_ssl.recv(1024).decode('utf-8')
                        print(respuesta_registro)

                        if "✅ Usuario registrado" in respuesta_registro:
                            # Si el registro fue exitoso, el servidor podría autenticar automáticamente
                            respuesta_auth = conexion_ssl.recv(1024).decode('utf-8')
                            print(respuesta_auth)

                            if "✅ Autenticación" in respuesta_auth:
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
