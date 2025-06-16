
import os
import sys
import time
import logging

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
logger = logging.getLogger(__name__)

# Importaciones de módulos propios
from cli.utils import calcular_hash_archivo
from cli.estilos import ANSI_VERDE, ANSI_RESET, ANSI_ROJO, ANSI_AMARILLO
from cli.mensajes import (MENSAJE_ENVIO_HASH, MENSAJE_VERIFICANDO, MENSAJE_VERIFICACION_COMPLETA,
                         MENSAJE_INTEGRIDAD_OK, MENSAJE_INTEGRIDAD_ERROR, MENSAJE_ANTIVIRUS_OK,
                         MENSAJE_ANTIVIRUS_ERROR, MENSAJE_VERIFICACION_PENDIENTE)
from .utilidades import enviar_mensaje, enviar_comando

# Constantes
BUFFER_SIZE = 1024  # Tamaño del buffer para recibir datos
DIRECTORIO_BASE = os.getenv("CLIENTE_DIR", "servidorArchivos")

def procesar_comandos(conexion):

    while True:
        prompt = conexion.recv(BUFFER_SIZE).decode('utf-8')
        comando = input(prompt)

        # Procesar comando especial SUBIR para añadir hash y enviar contenido
        if comando.upper().startswith("SUBIR "):
            comando = procesar_comando_crear(comando, conexion)
            # Si el comando es None, ya se manejó la respuesta
            if comando is None:
                continue

        # Procesar comando especial DESCARGAR para recibir archivos
        elif comando.upper().startswith("DESCARGAR "):
            procesar_comando_descargar(comando, conexion)
            continue

        # Procesar comando SALIR
        elif comando.upper() == "SALIR":
            enviar_comando(conexion, comando)
            respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
            print(respuesta)
            break

        # Procesar otros comandos
        else:
            enviar_comando(conexion, comando)
            respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
            print(respuesta)

def verificar_estado_archivo(conexion, nombre_archivo, max_intentos=3, espera_entre_intentos=2):
    verificacion_completa = False
    integridad_ok = False
    antivirus_ok = False

    print(MENSAJE_VERIFICANDO)

    for intento in range(max_intentos):
        # Enviar comando de verificación
        enviar_comando(conexion, f"VERIFICAR {nombre_archivo}")

        # Recibir respuesta
        respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
        print(f"{ANSI_AMARILLO}⏳ Intento {intento + 1}/{max_intentos}: Verificando estado...{ANSI_RESET}")

        # Verificar si la verificación está completa
        if "Verificación completa" in respuesta:
            verificacion_completa = True

            # Verificar integridad
            if "Integridad: OK" in respuesta:
                integridad_ok = True
                print(MENSAJE_INTEGRIDAD_OK)
            else:
                print(MENSAJE_INTEGRIDAD_ERROR)

            # Verificar antivirus
            if "Antivirus: OK" in respuesta:
                antivirus_ok = True
                print(MENSAJE_ANTIVIRUS_OK)
            else:
                print(MENSAJE_ANTIVIRUS_ERROR)

            print(MENSAJE_VERIFICACION_COMPLETA)
            break
        else:
            print(MENSAJE_VERIFICACION_PENDIENTE)

            # Esperar antes del siguiente intento
            if intento < max_intentos - 1:
                time.sleep(espera_entre_intentos)

    return verificacion_completa, integridad_ok, antivirus_ok

def procesar_comando_descargar(comando, conexion):

    partes = comando.split()
    if len(partes) != 2:
        print(f"{ANSI_ROJO}❌ Formato incorrecto. Uso: DESCARGAR nombre_archivo{ANSI_RESET}")
        return

    nombre_archivo = partes[1]

    # Enviar comando al servidor
    enviar_comando(conexion, comando)

    # Recibir respuesta inicial
    respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')

    # Verificar si el servidor está listo para enviar
    if not respuesta.startswith("✅ Listo para enviar"):
        print(respuesta)
        return

    print(f"{ANSI_VERDE}{respuesta}{ANSI_RESET}")

    # Extraer tamaño del archivo de la respuesta
    try:
        import re
        tamaño_match = re.search(r'\((\d+) bytes\)', respuesta)
        if tamaño_match:
            tamaño_esperado = int(tamaño_match.group(1))
        else:
            tamaño_esperado = 0
    except Exception:
        tamaño_esperado = 0

    # Crear directorio de destino si no existe
    if not os.path.exists(DIRECTORIO_BASE):
        os.makedirs(DIRECTORIO_BASE)

    # Ruta completa del archivo de destino
    ruta_destino = os.path.join(DIRECTORIO_BASE, nombre_archivo)

    # Confirmar que estamos listos para recibir
    enviar_mensaje(conexion, "LISTO")

    try:
        # Recibir y guardar el archivo
        bytes_recibidos = 0
        with open(ruta_destino, 'wb') as f:
            while bytes_recibidos < tamaño_esperado:
                # Calcular tamaño del chunk a recibir
                chunk_size = min(8192, tamaño_esperado - bytes_recibidos)

                # Recibir chunk
                chunk = conexion.recv(chunk_size)
                if not chunk:
                    break

                # Escribir chunk al archivo
                f.write(chunk)
                bytes_recibidos += len(chunk)

                # Mostrar progreso
                if tamaño_esperado > 0:
                    porcentaje = (bytes_recibidos / tamaño_esperado) * 100
                    print(f"\r📥 Descargando: {porcentaje:.1f}% ({bytes_recibidos}/{tamaño_esperado} bytes)", end="")

        print()  # Nueva línea después de la barra de progreso

        # Verificar si recibimos todos los bytes esperados
        if tamaño_esperado > 0 and bytes_recibidos < tamaño_esperado:
            print(f"{ANSI_AMARILLO}⚠️ Advertencia: Se recibieron menos bytes de los esperados ({bytes_recibidos}/{tamaño_esperado}){ANSI_RESET}")

        # Enviar confirmación al servidor
        enviar_mensaje(conexion, f"✅ Archivo '{nombre_archivo}' recibido correctamente ({bytes_recibidos} bytes)")

        print(f"{ANSI_VERDE}✅ Archivo guardado en {ruta_destino}{ANSI_RESET}")

    except Exception as e:
        print(f"{ANSI_ROJO}❌ Error al recibir el archivo: {e}{ANSI_RESET}")
        # Intentar enviar mensaje de error al servidor
        try:
            enviar_mensaje(conexion, f"❌ Error al recibir el archivo: {e}")
        except:
            pass

def procesar_comando_crear(comando, conexion):

    partes = comando.split()
    if len(partes) < 2:
        print(f"{ANSI_ROJO}❌ Formato incorrecto. Uso: SUBIR nombre_archivo{ANSI_RESET}")
        return comando

    accion = partes[0].upper()
    nombre_archivo = partes[1]

    # Bucle para reintentar si el archivo no existe
    while True:
        # Verificar si el archivo existe
        ruta_archivo = os.path.join(DIRECTORIO_BASE, nombre_archivo)
        if not os.path.exists(ruta_archivo):
            ruta_archivo = nombre_archivo  # Intentar con ruta relativa
            if not os.path.exists(ruta_archivo):
                print(f"{ANSI_ROJO}❌ No se encontró el archivo '{nombre_archivo}'{ANSI_RESET}")

                # Preguntar al usuario si desea intentar con otro archivo
                respuesta = input("¿Desea intentar con otro archivo? (s/n): ").lower()
                if respuesta != 's':
                    return None  # El usuario no quiere reintentar

                # Solicitar nuevo nombre de archivo
                nombre_archivo = input("Ingrese el nombre del archivo: ")
                continue  # Volver al inicio del bucle para verificar el nuevo archivo

        # Si llegamos aquí, el archivo existe, continuamos con el proceso
        break

    # Calcular hash del archivo
    hash_archivo = calcular_hash_archivo(ruta_archivo)
    if not hash_archivo:
        print(f"{ANSI_ROJO}❌ No se pudo calcular el hash del archivo{ANSI_RESET}")
        return None

    # Modificar el comando para incluir el hash
    comando_modificado = f"{accion} {nombre_archivo} {hash_archivo}"

    # Enviar comando al servidor
    print(MENSAJE_ENVIO_HASH)
    enviar_comando(conexion, comando_modificado)

    # Recibir respuesta inicial
    respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')

    # Verificar si el servidor está listo para recibir
    if not respuesta.startswith("✅ Listo para recibir"):
        print(respuesta)
        return None

    print(f"{ANSI_VERDE}{respuesta}{ANSI_RESET}")

    try:
        # Obtener tamaño del archivo
        tamaño_archivo = os.path.getsize(ruta_archivo)

        # Enviar tamaño del archivo
        enviar_mensaje(conexion, str(tamaño_archivo))

        # Enviar contenido del archivo
        bytes_enviados = 0
        with open(ruta_archivo, 'rb') as f:
            while True:
                # Leer chunk del archivo
                chunk = f.read(8192)  # 8KB chunks
                if not chunk:
                    break

                # Enviar chunk
                conexion.sendall(chunk)
                bytes_enviados += len(chunk)

                # Mostrar progreso
                porcentaje = (bytes_enviados / tamaño_archivo) * 100
                print(f"\r📤 Subiendo: {porcentaje:.1f}% ({bytes_enviados}/{tamaño_archivo} bytes)", end="")

        print()  # Nueva línea después de la barra de progreso

        # Recibir confirmación del servidor
        respuesta = conexion.recv(BUFFER_SIZE).decode('utf-8')
        print(respuesta)

        # Verificar estado del archivo (integridad y antivirus)
        verificar_estado_archivo(conexion, nombre_archivo)

    except Exception as e:
        print(f"{ANSI_ROJO}❌ Error al enviar el archivo: {e}{ANSI_RESET}")

    return None  # Indicar que ya se manejó la respuesta
