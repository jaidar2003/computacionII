import socket
import ssl
import os
import logging
import subprocess
from comandos import manejar_comando
from seguridad import autenticar_usuario_en_servidor, registrar_usuario

DIRECTORIO_BASE = "servidorArchivos"

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
