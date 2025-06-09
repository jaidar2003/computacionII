# 🖥️ Cliente para el Servidor de Archivos
# Cliente de línea de comandos con conexión SSL, autenticación de usuarios,
# registro de usuarios y operaciones con archivos (listar, crear, eliminar, renombrar).

import socket
import ssl
import sys
import os
import logging
import datetime
from dotenv import load_dotenv

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from server.comandos import manejar_comando
from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario
from cli.utils import input_password, calcular_hash_archivo
from cli.interface import mostrar_banner, mostrar_menu_principal, mostrar_comandos_disponibles
from cli.mensajes import (ERROR_CREDENCIALES_INVALIDAS, MENSAJE_DESCONECTAR, MENSAJE_ENVIO_HASH,
                         MENSAJE_VERIFICANDO, MENSAJE_VERIFICACION_COMPLETA, MENSAJE_INTEGRIDAD_OK,
                         MENSAJE_INTEGRIDAD_ERROR, MENSAJE_ANTIVIRUS_OK, MENSAJE_ANTIVIRUS_ERROR,
                         MENSAJE_VERIFICACION_PENDIENTE)
from cli.estilos import ANSI_VERDE, ANSI_RESET, ANSI_ROJO, ANSI_AMARILLO
import time


# 🔧 Constantes
DIRECTORIO_BASE = os.getenv("CLIENTE_DIR", "servidorArchivos")
BUFFER_SIZE = 1024  # Tamaño del buffer para recibir datos
DIAS_AVISO_EXPIRACION = 30  # Días antes de expiración para mostrar advertencia

def _verificar_certificado_servidor():
    """🔍 Verifica validez y expiración del certificado del servidor.
    Returns: (es_valido, mensaje)"""
    cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "certificados", "certificado.pem")

    if not os.path.exists(cert_path):
        return False, f"⚠️ No se encontró el certificado del servidor en {cert_path}"

    try:
        # Leer el contenido del certificado
        with open(cert_path, 'r') as f:
            cert_data = f.read()

        # Crear un contexto SSL temporal para analizar el certificado
        context = ssl.create_default_context()
        context.load_verify_locations(cadata=cert_data)

        # Obtener información del certificado
        cert = ssl._ssl._test_decode_cert(cert_path)

        # Extraer fecha de expiración
        not_after = cert.get('notAfter', '')
        if not not_after:
            return False, "⚠️ No se pudo determinar la fecha de expiración del certificado"

        # Formato de fecha en certificados: 'May 30 00:00:00 2023 GMT'
        try:
            expiracion = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            hoy = datetime.datetime.now()

            # Verificar si ya expiró
            if hoy > expiracion:
                return False, f"❌ El certificado del servidor ha expirado el {not_after}"

            # Verificar si está por expirar
            dias_restantes = (expiracion - hoy).days
            if dias_restantes <= DIAS_AVISO_EXPIRACION:
                return True, f"⚠️ El certificado del servidor expirará en {dias_restantes} días ({not_after})"

            # Certificado válido
            return True, f"✅ Certificado del servidor válido hasta {not_after}"

        except ValueError as e:
            return False, f"⚠️ Error al analizar la fecha de expiración del certificado: {e}"

    except Exception as e:
        return False, f"❌ Error al verificar el certificado del servidor: {e}"

def iniciar_cliente(host, port):
    """🚀 Inicia cliente y conecta al servidor en host:port."""
    logger.info(f"🌐 Iniciando cliente para conectar a {host}:{port}")

    # Verificar el certificado del servidor antes de conectar
    cert_valido, cert_mensaje = _verificar_certificado_servidor()

    # Inicializar respuesta con un valor por defecto
    respuesta = ''

    # Mostrar información sobre el certificado
    if cert_valido:
        if "expirará" in cert_mensaje:
            print(f"{ANSI_AMARILLO}{cert_mensaje}{ANSI_RESET}")
        else:
            print(f"{ANSI_VERDE}{cert_mensaje}{ANSI_RESET}")
    else:
        print(f"{ANSI_ROJO}{cert_mensaje}{ANSI_RESET}")
        print(f"{ANSI_AMARILLO}⚠️ La conexión podría no ser segura. ¿Desea continuar? (s/n){ANSI_RESET}")
        respuesta = input().lower()
        if respuesta != 's' and respuesta != 'si':
            print(f"{ANSI_ROJO}❌ Conexión cancelada por el usuario.{ANSI_RESET}")
            return

    try:
        # 🔒 Configurar contexto SSL
        try:
            # Determinar si se debe verificar el certificado basado en la validez y la respuesta del usuario
            verificar = cert_valido
            if not cert_valido and respuesta in ('s', 'si'):
                verificar = False
                logger.warning("⚠️ Usuario eligió continuar sin verificación de certificado")

            conexion_ssl = _establecer_conexion_ssl(host, port, verificar_cert=verificar)
        except ssl.SSLError as ssl_error:
            logger.error(f"❌ Error de seguridad SSL: {ssl_error}")
            print(f"{ANSI_ROJO}❌ Error de seguridad en la conexión SSL: {ssl_error}{ANSI_RESET}")
            print(f"{ANSI_ROJO}❌ No se pudo verificar la identidad del servidor.{ANSI_RESET}")
            print(f"{ANSI_AMARILLO}⚠️ Esto podría indicar un problema con el certificado o un intento de ataque.{ANSI_RESET}")
            return
        except ConnectionRefusedError:
            logger.error(f"❌ No se pudo conectar a {host}:{port}. Servidor no disponible.")
            print(f"{ANSI_ROJO}❌ No se pudo conectar a {host}:{port}.{ANSI_RESET}")
            print(f"{ANSI_ROJO}❌ El servidor no está disponible o la dirección/puerto son incorrectos.{ANSI_RESET}")
            return
        except Exception as conn_error:
            logger.error(f"❌ Error al establecer conexión: {conn_error}")
            print(f"{ANSI_ROJO}❌ Error al establecer conexión: {conn_error}{ANSI_RESET}")
            return

        # 👋 Recibir mensajes de bienvenida
        _recibir_mensajes_bienvenida(conexion_ssl)

        # 🔑 Autenticar o registrar usuario
        if not _manejar_autenticacion(conexion_ssl):
            return

        # 💻 Procesar comandos del usuario
        _procesar_comandos(conexion_ssl)

    except Exception as error:
        logger.error(f"❌ Error en el cliente: {error}")
        print(f"{ANSI_ROJO}❌ Error: {error}{ANSI_RESET}")

def _establecer_conexion_ssl(host, port, verificar_cert=True):
    """🔒 Establece conexión SSL con el servidor, opcionalmente verificando su certificado.
    Returns: Socket SSL conectado"""
    # Configurar contexto SSL con verificación de certificado
    contexto = ssl.create_default_context()

    # Configurar verificación según el parámetro
    if verificar_cert:
        # Habilitar verificación de certificado
        contexto.verify_mode = ssl.CERT_REQUIRED

        # Habilitar verificación de hostname si estamos usando un nombre de dominio
        if not host.replace('.', '').isdigit():  # Si no es una IP
            contexto.check_hostname = True
        else:
            contexto.check_hostname = False

        # Cargar el certificado del servidor como certificado de confianza
        cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               "certificados", "certificado.pem")

        if os.path.exists(cert_path):
            contexto.load_verify_locations(cafile=cert_path)
            print(f"{ANSI_VERDE}✅ Certificado del servidor cargado correctamente.{ANSI_RESET}")
        else:
            print(f"{ANSI_AMARILLO}⚠️ No se encontró el certificado del servidor en {cert_path}{ANSI_RESET}")
            print(f"{ANSI_AMARILLO}⚠️ La conexión no será segura sin verificación de certificado.{ANSI_RESET}")
            # Fallback a modo sin verificación si no encontramos el certificado
            contexto.check_hostname = False
            contexto.verify_mode = ssl.CERT_NONE
    else:
        # Deshabilitar verificación de certificado si el usuario eligió continuar sin verificar
        print(f"{ANSI_AMARILLO}⚠️ Verificación de certificado deshabilitada por el usuario.{ANSI_RESET}")
        print(f"{ANSI_AMARILLO}⚠️ La conexión no será segura.{ANSI_RESET}")
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE

    try:
        # Establecer conexión
        sock = socket.create_connection((host, port))
        # Configurar timeout para operaciones de socket (120 segundos)
        sock.settimeout(120)
        conexion_ssl = contexto.wrap_socket(sock, server_hostname=host)

        # Verificar y mostrar información del certificado
        cert = conexion_ssl.getpeercert()
        if cert:
            subject = dict(x[0] for x in cert['subject'])
            issuer = dict(x[0] for x in cert['issuer'])
            print(f"🔒 Conectado a servidor con certificado:")
            print(f"   - Emitido para: {subject.get('commonName', 'Desconocido')}")
            print(f"   - Emitido por: {issuer.get('commonName', 'Desconocido')}")
            print(f"   - Válido hasta: {cert.get('notAfter', 'Desconocido')}")

        logger.debug(f"🔌 Conexión segura establecida con {host}:{port}")
        return conexion_ssl

    except ssl.SSLError as e:
        print(f"❌ Error de verificación SSL: {e}")
        print("❌ No se pudo verificar la identidad del servidor.")
        print("❌ Esto podría indicar un intento de ataque 'man-in-the-middle'.")
        raise
    except Exception as e:
        print(f"❌ Error al establecer conexión: {e}")
        raise

def _recibir_mensajes_bienvenida(conexion):
    # 👋 Recibe y muestra mensajes de bienvenida
    mensaje = conexion.recv(BUFFER_SIZE).decode('utf-8')
    print(ANSI_VERDE + mensaje + ANSI_RESET)

def _manejar_autenticacion(conexion):
    # 🔑 Maneja autenticación o registro. Retorna True si exitoso
    while True:
        mostrar_menu_principal()
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            # 🔑 Iniciar sesión
            if _iniciar_sesion(conexion):
                return True

        elif opcion == '2':
            # 📝 Registrar nuevo usuario
            _registrar_usuario(conexion)

        elif opcion == '3':
            # 🚪 Salir
            _enviar_comando(conexion, "SALIR")
            print(MENSAJE_DESCONECTAR)
            return False

        else:
            print(f"❌ Opción no válida: {opcion}")

def _iniciar_sesion(conexion):
    # 🔑 Inicia sesión. Retorna True si exitoso
    conexion.recv(BUFFER_SIZE)  # Descartar el prompt "Usuario: " del servidor

    # Solicitar credenciales
    usuario = input("Usuario: ")
    _enviar_mensaje(conexion, f"{usuario}")
    conexion.recv(BUFFER_SIZE)  # Recibir prompt de contraseña

    password = input_password("Contraseña: ")
    _enviar_mensaje(conexion, f"{password}")

    # Verificar respuesta
    respuesta_auth = conexion.recv(BUFFER_SIZE).decode('utf-8')
    if "✅ Autenticación exitosa" in respuesta_auth:
        print(ANSI_VERDE + respuesta_auth + ANSI_RESET)
        mostrar_comandos_disponibles("lectura")
        return True
    else:
        print(ANSI_ROJO + ERROR_CREDENCIALES_INVALIDAS + ANSI_RESET)
        return False

def _registrar_usuario(conexion):
    # 📝 Registra nuevo usuario
    nuevo_usuario = input("Nuevo usuario: ")
    nueva_password = input_password("Nueva contraseña: ")

    _enviar_comando(conexion, f"REGISTRAR {nuevo_usuario} {nueva_password}")
    respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')

    if "✅" in respuesta:
        print(ANSI_VERDE + respuesta + ANSI_RESET)
        print(ANSI_VERDE + "👤 Por favor, inicie sesión con sus nuevas credenciales." + ANSI_RESET)
    else:
        print(ANSI_ROJO + respuesta + ANSI_RESET)

def _procesar_comandos(conexion):
    # 💻 Procesa comandos del usuario
    while True:
        prompt = conexion.recv(BUFFER_SIZE).decode('utf-8')
        comando = input(prompt)

        # Procesar comando especial CREAR para añadir hash y enviar contenido
        if comando.upper().startswith("CREAR ") or comando.upper().startswith("SUBIR "):
            comando = _procesar_comando_crear(comando, conexion)
            # Si el comando es None, ya se manejó la respuesta
            if comando is None:
                continue

        # Procesar comando especial DESCARGAR para recibir archivos
        elif comando.upper().startswith("DESCARGAR "):
            _procesar_comando_descargar(comando, conexion)
            continue

        _enviar_mensaje(conexion, comando)

        if comando.upper() == "SALIR":
            print(MENSAJE_DESCONECTAR)
            break

        respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
        print(respuesta)

def _verificar_estado_archivo(conexion, nombre_archivo, max_intentos=3, espera_entre_intentos=2):
    # 🔍 Verifica estado del archivo (integridad y antivirus). Retorna True si exitoso
    logger.info(f"🔍 Verificando estado del archivo: {nombre_archivo}")

    for intento in range(max_intentos):
        # Enviar comando VERIFICAR
        _enviar_comando(conexion, f"VERIFICAR {nombre_archivo}")

        # Recibir respuesta
        respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')

        # Analizar la respuesta
        if "No hay información de verificación" in respuesta or "verificación para" not in respuesta:
            print(MENSAJE_VERIFICACION_PENDIENTE.format(archivo=nombre_archivo))
            time.sleep(espera_entre_intentos)
            continue

        # Mostrar encabezado de verificación
        print(ANSI_VERDE + MENSAJE_VERIFICACION_COMPLETA.format(archivo=nombre_archivo) + ANSI_RESET)

        # Verificar integridad
        if "Integridad: válida" in respuesta:
            print(ANSI_VERDE + MENSAJE_INTEGRIDAD_OK + ANSI_RESET)
            integridad_ok = True
        else:
            print(ANSI_ROJO + MENSAJE_INTEGRIDAD_ERROR + ANSI_RESET)
            integridad_ok = False

        # Verificar antivirus
        if "Antivirus: limpio" in respuesta:
            print(ANSI_VERDE + MENSAJE_ANTIVIRUS_OK + ANSI_RESET)
            antivirus_ok = True
        else:
            print(ANSI_ROJO + MENSAJE_ANTIVIRUS_ERROR + ANSI_RESET)
            antivirus_ok = False

        return integridad_ok and antivirus_ok

    # Si llegamos aquí, no se pudo obtener la verificación después de varios intentos
    print(MENSAJE_VERIFICACION_PENDIENTE.format(archivo=nombre_archivo))
    return False

def _procesar_comando_descargar(comando, conexion):
    # 📥 Procesa comando DESCARGAR, recibe archivo del servidor y lo guarda localmente
    partes = comando.split()
    if len(partes) < 2:
        print(f"{ANSI_ROJO}❌ Formato incorrecto. Uso: DESCARGAR nombre_archivo{ANSI_RESET}")
        return

    nombre_archivo = partes[1]

    # Preguntar dónde guardar el archivo
    ruta_destino = input(f"Ruta local donde guardar '{nombre_archivo}' (Enter para usar el nombre original): ")
    if not ruta_destino:
        ruta_destino = nombre_archivo

    if os.path.isdir(ruta_destino):
        ruta_destino = os.path.join(ruta_destino, nombre_archivo)
        print(f"{ANSI_AMARILLO}ℹ️ Guardando en: {ruta_destino}{ANSI_RESET}")

    # Asegurar que el directorio padre existe
    directorio_padre = os.path.dirname(ruta_destino)
    if directorio_padre and not os.path.exists(directorio_padre):
        try:
            os.makedirs(directorio_padre)
            print(f"{ANSI_VERDE}✅ Directorio creado: {directorio_padre}{ANSI_RESET}")
        except Exception as e:
            print(f"{ANSI_ROJO}❌ No se pudo crear el directorio: {e}{ANSI_RESET}")
            return

    # Enviar comando al servidor
    _enviar_mensaje(conexion, comando)

    # Recibir respuesta inicial del servidor
    respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
    print(respuesta)

    if "✅ Listo para enviar" not in respuesta:
        return

    # Extraer tamaño del archivo de la respuesta
    try:
        import re
        match = re.search(r'\((\d+) bytes\)', respuesta)
        if match:
            file_size = int(match.group(1))
        else:
            file_size = 0
            print(f"{ANSI_AMARILLO}⚠️ No se pudo determinar el tamaño del archivo.{ANSI_RESET}")
    except Exception as e:
        file_size = 0
        print(f"{ANSI_AMARILLO}⚠️ Error al procesar tamaño: {e}{ANSI_RESET}")

    _enviar_mensaje(conexion, "LISTO")

    print(f"{ANSI_AMARILLO}📥 Recibiendo archivo '{nombre_archivo}'...{ANSI_RESET}")

    try:
        # Recibir y guardar el archivo
        with open(ruta_destino, 'wb') as f:
            bytes_recibidos = 0
            chunk_size = 8192  # 8KB chunks

            while bytes_recibidos < file_size:
                bytes_restantes = file_size - bytes_recibidos
                chunk_actual = min(chunk_size, bytes_restantes)

                chunk = conexion.recv(chunk_actual)
                if not chunk:  # Conexión cerrada por el servidor
                    raise ConnectionError("Conexión cerrada por el servidor durante la transferencia")

                f.write(chunk)
                bytes_recibidos += len(chunk)

                if file_size > 0:
                    porcentaje = int(bytes_recibidos * 100 / file_size)
                    print(f"\r📥 Recibiendo: {bytes_recibidos}/{file_size} bytes ({porcentaje}%)", end="")
                else:
                    print(f"\r📥 Recibiendo: {bytes_recibidos} bytes", end="")

            print("\n✅ Descarga completada.")

        # Enviar confirmación al servidor
        _enviar_mensaje(conexion, "✅ Archivo recibido correctamente")

    except socket.timeout:
        print(f"\n{ANSI_ROJO}❌ Error: Tiempo de espera agotado durante la transferencia.{ANSI_RESET}")
        _enviar_mensaje(conexion, "❌ Error: Tiempo de espera agotado")
        # Eliminar archivo parcial
        if os.path.exists(ruta_destino):
            os.remove(ruta_destino)

    except ConnectionError as e:
        print(f"\n{ANSI_ROJO}❌ Error de conexión durante la transferencia: {e}{ANSI_RESET}")
        # Eliminar archivo parcial
        if os.path.exists(ruta_destino):
            os.remove(ruta_destino)

    except Exception as e:
        print(f"\n{ANSI_ROJO}❌ Error inesperado durante la transferencia: {e}{ANSI_RESET}")
        _enviar_mensaje(conexion, f"❌ Error: {str(e)}")
        # Eliminar archivo parcial
        if os.path.exists(ruta_destino):
            os.remove(ruta_destino)

def _procesar_comando_crear(comando, conexion):
    # 📄 Procesa comando CREAR, añade hash y envía contenido. Retorna comando modificado o None
    partes = comando.split()
    if len(partes) == 2:
        archivo_local = input("Ruta al archivo local: ")
        if os.path.exists(archivo_local):
            # Calcular hash
            hash_archivo = calcular_hash_archivo(archivo_local)
            if hash_archivo:
                # Enviar comando con hash
                comando_modificado = f"{partes[0]} {partes[1]} {hash_archivo}"
                print(MENSAJE_ENVIO_HASH.format(comando=comando_modificado))
                _enviar_mensaje(conexion, comando_modificado)

                # Recibir respuesta inicial del servidor
                respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
                print(respuesta)

                # Si el servidor aceptó el comando, enviar el contenido del archivo
                if "✅" in respuesta:
                    print(f"{ANSI_AMARILLO}📤 Enviando contenido del archivo...{ANSI_RESET}")
                    try:
                        file_size = os.path.getsize(archivo_local)
                        _enviar_mensaje(conexion, str(file_size))

                        with open(archivo_local, 'rb') as f:
                            bytes_sent = 0
                            chunk_size = 8192  # 8KB chunks
                            while bytes_sent < file_size:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                conexion.sendall(chunk)
                                bytes_sent += len(chunk)
                                print(f"\r📤 Enviando: {bytes_sent}/{file_size} bytes ({int(bytes_sent*100/file_size)}%)", end="")
                            print("\n✅ Envío completado.")
                    except socket.timeout:
                        print(f"\n{ANSI_ROJO}❌ Error: Tiempo de espera agotado durante la transferencia. El servidor no responde.{ANSI_RESET}")
                        return None
                    except ConnectionError as e:
                        print(f"\n{ANSI_ROJO}❌ Error de conexión durante la transferencia: {e}{ANSI_RESET}")
                        return None
                    except Exception as e:
                        print(f"\n{ANSI_ROJO}❌ Error inesperado durante la transferencia: {e}{ANSI_RESET}")
                        return None

                    # Recibir confirmación final
                    try:
                        respuesta_final = conexion.recv(BUFFER_SIZE).decode('utf-8')
                        print(respuesta_final)

                        # Informar al usuario que se está verificando el archivo
                        print(f"{ANSI_AMARILLO}{MENSAJE_VERIFICANDO}{ANSI_RESET}")

                        # Esperar un momento para que el servidor inicie la verificación
                        time.sleep(1)

                        # Verificar el estado del archivo
                        _verificar_estado_archivo(conexion, partes[1])
                    except socket.timeout:
                        print(f"{ANSI_AMARILLO}⚠️ No se pudo recibir confirmación del servidor, pero el archivo podría haberse enviado correctamente.{ANSI_RESET}")
                    except Exception as e:
                        print(f"{ANSI_ROJO}❌ Error al recibir confirmación del servidor: {e}{ANSI_RESET}")

                    return None  # Ya manejamos la respuesta aquí

                return None  # Ya manejamos la respuesta

    # Si llegamos aquí, procesamos normalmente
    return comando

def _enviar_mensaje(conexion, mensaje):
    """📤 Envía mensaje al servidor"""
    conexion.sendall(f"{mensaje}\n".encode('utf-8'))

def _enviar_comando(conexion, comando):
    """📤 Envía comando al servidor"""
    logger.debug(f"📤 Enviando comando: {comando}")
    _enviar_mensaje(conexion, comando)


if __name__ == "__main__":
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "historyLogs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=os.path.join(log_dir, 'cliente.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    mostrar_banner()

    # Usar variables de entorno para host y puerto
    host = os.getenv("SERVIDOR_HOST", "127.0.0.1")
    port = int(os.getenv("SERVIDOR_PORT", 1608))

    cliente_host = "localhost" if host == "0.0.0.0" else host

    iniciar_cliente(cliente_host, port)
