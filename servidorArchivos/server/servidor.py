import socket
import ssl
import threading
import logging
import os
import sys
import argparse
from dotenv import load_dotenv

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importaciones con manejo de errores
try:
    from server.comandos import manejar_comando
    from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from comandos import manejar_comando
    from seguridad import autenticar_usuario_en_servidor, registrar_usuario

from baseDeDatos.db import log_evento
from utils.config import SERVIDOR_HOST, SERVIDOR_PORT, SERVIDOR_DIR, CERT_PATH, KEY_PATH
from utils.config import crear_directorio_si_no_existe, configurar_argumentos
from utils.network import crear_socket_servidor, configurar_contexto_ssl

load_dotenv()

# Configuración de logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "historial")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'servidor.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def manejar_cliente(conexion_ssl, direccion, directorio):
    try:
        # 👋 Enviar mensaje de bienvenida
        _enviar_mensaje(conexion_ssl, "🌍 Bienvenido al servidor de archivos seguro.\n")

        # 🔐 Autenticar al usuario
        usuario_id, permisos = _autenticar_usuario(conexion_ssl)

        # 💻 Procesar comandos del usuario
        _procesar_comandos(conexion_ssl, directorio, usuario_id)

    except Exception as error:
        logging.error(f"❌ Error con cliente {direccion}: {error}")
    finally:
        conexion_ssl.close()
        logging.info(f"🔌 Cliente {direccion} desconectado")

def _enviar_mensaje(conexion, mensaje):
    conexion.sendall(mensaje.encode('utf-8'))

def _recibir_mensaje(conexion, prompt=None):
    if prompt:
        _enviar_mensaje(conexion, prompt)
    return conexion.recv(1024).decode().strip()

def _autenticar_usuario(conexion):
    while True:
        usuario = _recibir_mensaje(conexion, "👤 Usuario: ")

        # 📝 Manejar comando de registro
        if usuario.upper().startswith("REGISTRAR"):
            _manejar_registro(conexion, usuario)
            continue

        # 🔒 Autenticar usuario existente
        password = _recibir_mensaje(conexion, "🔒 Contraseña: ")

        datos_usuario = autenticar_usuario_en_servidor(usuario, password)
        if not datos_usuario:
            _enviar_mensaje(conexion, "❌ Credenciales inválidas. Intenta nuevamente.\n")
            continue

        usuario_id, permisos = datos_usuario
        _enviar_mensaje(conexion, f"✅ Autenticación exitosa! Permisos: {permisos}\n")
        return usuario_id, permisos

def _manejar_registro(conexion, comando_registro):
    partes = comando_registro.split()
    if len(partes) != 3:
        _enviar_mensaje(conexion, "❌ Formato incorrecto. Usa: REGISTRAR usuario contraseña\n")
        return

    _, nuevo_usuario, nueva_contraseña = partes
    respuesta = registrar_usuario(nuevo_usuario, nueva_contraseña)
    _enviar_mensaje(conexion, f"{respuesta}\n")

    if respuesta.startswith("✅"):
        _enviar_mensaje(conexion, "👤 Ahora inicia sesión con tu nuevo usuario.\n")

def _procesar_comandos(conexion, directorio, usuario_id):
    while True:
        comando = _recibir_mensaje(conexion, "\n💻 Ingresar comando ('SALIR' para desconectar): ")

        if comando.upper() == "SALIR":
            _enviar_mensaje(conexion, "🔌 Desconectando...\n")
            break

        # Verificar si es un comando que requiere conexión
        partes = comando.strip().split()
        if partes and partes[0].upper() in ["DESCARGAR", "SUBIR"]:
            respuesta = manejar_comando(comando, directorio, usuario_id, conexion)
        else:
            respuesta = manejar_comando(comando, directorio, usuario_id)

        _enviar_mensaje(conexion, f"📄 {respuesta}\n")


def iniciar_servidor(host=SERVIDOR_HOST, port=SERVIDOR_PORT, directorio=SERVIDOR_DIR):
    # Asegurar que el directorio existe
    crear_directorio_si_no_existe(directorio)

    try:
        # Configurar socket para soportar IPv4 e IPv6
        servidor = crear_socket_servidor(host, port)
        print(f"🌍 Servidor de Archivos Seguro escuchando en {host}:{port}")

        # Configurar SSL
        contexto = configurar_contexto_ssl(CERT_PATH, KEY_PATH)

        # Aceptar conexiones
        while True:
            cliente, direccion = servidor.accept()
            logging.info(f"🔌 Nueva conexión desde {direccion}")

            try:
                # Envolver la conexión con SSL
                cliente_ssl = contexto.wrap_socket(cliente, server_side=True)

                # Crear un hilo para manejar al cliente
                hilo_cliente = threading.Thread(
                    target=manejar_cliente,
                    args=(cliente_ssl, direccion, directorio)
                )
                hilo_cliente.daemon = True
                hilo_cliente.start()

            except ssl.SSLError as error:
                logging.error(f"🔒 Error SSL con {direccion}: {error}")
                cliente.close()

    except KeyboardInterrupt:
        logging.info("👋 Servidor detenido por el usuario")
        print("\n👋 Servidor detenido. ¡Hasta pronto!")
    except Exception as error:
        logging.error(f"❌ Error en el servidor: {error}")
    finally:
        if 'servidor' in locals():
            servidor.close()

# La función configurar_argumentos se ha movido a utils/config.py

if __name__ == "__main__":
    # 📋 Verificar que los módulos se importaron correctamente
    print("✅ Módulo servidor.py cargado correctamente.")
    print("✅ Importación de comandos, seguridad y baseDeDatos.db exitosa.")

    # 🔧 Configurar argumentos
    args = configurar_argumentos(modo_dual=False)

    # 📝 Configurar nivel de logging si es verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 🚀 Iniciar servidor
    iniciar_servidor(args.host, args.port, args.directorio)
