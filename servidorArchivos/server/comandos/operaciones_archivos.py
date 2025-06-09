"""
Operaciones con archivos del servidor.

Este módulo contiene todas las funciones relacionadas con operaciones
de archivos en el servidor, como listar, crear, eliminar, renombrar,
descargar y verificar archivos.
"""

import os
import sys
import socket

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tareas.celery import verificar_integridad_y_virus
from baseDeDatos.db import obtener_conexion
from .utilidades import _enviar_mensaje

def listar_archivos(directorio_base):
    """
    Lista todos los archivos en el directorio base.

    Args:
        directorio_base (str): Directorio base para operaciones con archivos

    Returns:
        str: Lista formateada de archivos o mensaje de error
    """
    try:
        archivos = os.listdir(directorio_base)
        if not archivos:
            return "📂 No hay archivos en el servidor."

        # Formatear la lista de archivos para mejor visualización
        archivos_formateados = [f"📄 {archivo}" for archivo in archivos]
        return "\n".join(archivos_formateados)
    except Exception as error:
        return f"❌ Error al listar archivos: {error}"

def crear_archivo(directorio_base, nombre_archivo, hash_esperado=None, conexion=None):
    """
    Crea un archivo en el servidor, opcionalmente recibiendo su contenido.

    Args:
        directorio_base (str): Directorio base para operaciones con archivos
        nombre_archivo (str): Nombre del archivo a crear
        hash_esperado (str, optional): Hash esperado para verificación de integridad
        conexion (socket, optional): Conexión para recibir el contenido del archivo

    Returns:
        str: Mensaje de resultado de la operación
    """
    try:
        # Validar nombre de archivo
        if not _es_nombre_archivo_valido(nombre_archivo):
            return "❌ Nombre de archivo inválido. No debe contener caracteres especiales."

        # Construir ruta completa
        ruta = os.path.join(directorio_base, nombre_archivo)

        # Verificar si ya existe
        if os.path.exists(ruta):
            return f"⚠️ El archivo '{nombre_archivo}' ya existe."

        # Si tenemos hash y conexión, esperamos recibir el contenido del archivo
        if hash_esperado and conexion:
            # Enviar mensaje de aceptación
            _enviar_mensaje(conexion, f"✅ Listo para recibir '{nombre_archivo}'")

            # Recibir tamaño del archivo
            tamaño = int(conexion.recv(1024).decode().strip())

            # Recibir contenido del archivo y escribir directamente a disco
            bytes_recibidos = 0
            try:
                with open(ruta, 'wb') as f:
                    while bytes_recibidos < tamaño:
                        chunk_size = min(8192, tamaño - bytes_recibidos)
                        try:
                            chunk = conexion.recv(chunk_size)
                            if not chunk:  # Conexión cerrada por el cliente
                                raise ConnectionError("Conexión cerrada por el cliente durante la transferencia")
                            f.write(chunk)
                            bytes_recibidos += len(chunk)
                        except socket.timeout:
                            raise TimeoutError("Tiempo de espera agotado durante la recepción del archivo")
            except (TimeoutError, ConnectionError, OSError) as e:
                # Eliminar el archivo parcial si hubo un error
                if os.path.exists(ruta):
                    os.remove(ruta)
                raise Exception(f"Error durante la recepción del archivo: {str(e)}")

            # Enviar confirmación
            _enviar_mensaje(conexion, f"✅ Archivo '{nombre_archivo}' recibido correctamente ({bytes_recibidos} bytes)")
        else:
            # Crear archivo vacío (comportamiento actual)
            with open(ruta, 'w') as _:
                pass

        # Iniciar verificación en segundo plano
        _iniciar_verificacion(ruta, hash_esperado)

        # Retornar mensaje apropiado (solo si no enviamos ya una respuesta)
        if not (hash_esperado and conexion):
            if hash_esperado:
                return f"✅ Archivo '{nombre_archivo}' creado y enviado para verificación con hash."
            else:
                return f"✅ Archivo '{nombre_archivo}' creado y enviado para verificación."

    except Exception as error:
        return f"❌ Error al crear archivo: {error}"

def eliminar_archivo(directorio_base, nombre_archivo):
    """
    Elimina un archivo del servidor.

    Args:
        directorio_base (str): Directorio base para operaciones con archivos
        nombre_archivo (str): Nombre del archivo a eliminar

    Returns:
        str: Mensaje de resultado de la operación
    """
    try:
        # Validar nombre de archivo
        if not _es_nombre_archivo_valido(nombre_archivo):
            return "❌ Nombre de archivo inválido. No debe contener caracteres especiales."

        # Construir ruta completa
        ruta = os.path.join(directorio_base, nombre_archivo)

        # Verificar si existe
        if not os.path.exists(ruta):
            return f"⚠️ Archivo '{nombre_archivo}' no encontrado."

        # Eliminar archivo
        os.remove(ruta)
        return f"🗑️ Archivo '{nombre_archivo}' eliminado correctamente."
    except Exception as error:
        return f"❌ Error al eliminar archivo: {error}"

def renombrar_archivo(directorio_base, nombre_viejo, nombre_nuevo):
    """
    Renombra un archivo en el servidor.

    Args:
        directorio_base (str): Directorio base para operaciones con archivos
        nombre_viejo (str): Nombre actual del archivo
        nombre_nuevo (str): Nuevo nombre para el archivo

    Returns:
        str: Mensaje de resultado de la operación
    """
    try:
        # Validar nombres de archivo
        if not _es_nombre_archivo_valido(nombre_viejo) or not _es_nombre_archivo_valido(nombre_nuevo):
            return "❌ Nombre de archivo inválido. No debe contener caracteres especiales."

        # Construir rutas completas
        ruta_vieja = os.path.join(directorio_base, nombre_viejo)
        ruta_nueva = os.path.join(directorio_base, nombre_nuevo)

        # Verificar si el archivo original existe
        if not os.path.exists(ruta_vieja):
            return f"⚠️ Archivo '{nombre_viejo}' no encontrado."

        # Verificar si el nuevo nombre ya existe
        if os.path.exists(ruta_nueva):
            return f"⚠️ Ya existe un archivo con el nombre '{nombre_nuevo}'."

        # Renombrar archivo
        os.rename(ruta_vieja, ruta_nueva)
        return f"✏️ Archivo '{nombre_viejo}' renombrado a '{nombre_nuevo}'."
    except Exception as error:
        return f"❌ Error al renombrar archivo: {error}"

def _es_nombre_archivo_valido(nombre):
    """
    Verifica si un nombre de archivo es válido.

    Args:
        nombre (str): Nombre de archivo a validar

    Returns:
        bool: True si el nombre es válido, False en caso contrario
    """
    # Caracteres prohibidos en nombres de archivo
    caracteres_prohibidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(c in nombre for c in caracteres_prohibidos)

def _iniciar_verificacion(ruta, hash_esperado=None):
    """
    Inicia la verificación de integridad y antivirus de un archivo.

    Args:
        ruta (str): Ruta completa al archivo
        hash_esperado (str, optional): Hash esperado para verificación de integridad
    """
    verificar_integridad_y_virus.delay(ruta, hash_esperado)

def descargar_archivo(directorio_base, nombre_archivo, conexion=None):
    """
    Envía un archivo al cliente para su descarga.

    Args:
        directorio_base (str): Directorio base para operaciones con archivos
        nombre_archivo (str): Nombre del archivo a descargar
        conexion (socket, optional): Conexión para enviar el contenido del archivo

    Returns:
        str: Mensaje de resultado de la operación
    """
    try:
        # Validar nombre de archivo
        if not _es_nombre_archivo_valido(nombre_archivo):
            return "❌ Nombre de archivo inválido. No debe contener caracteres especiales."

        # Construir ruta completa
        ruta = os.path.join(directorio_base, nombre_archivo)

        # Verificar si existe
        if not os.path.exists(ruta):
            return f"⚠️ Archivo '{nombre_archivo}' no encontrado."

        # Si no tenemos conexión, no podemos enviar el archivo
        if not conexion:
            return f"⚠️ No se puede descargar '{nombre_archivo}'. Conexión no disponible."

        try:
            # Obtener tamaño del archivo
            file_size = os.path.getsize(ruta)

            # Enviar mensaje de aceptación con el tamaño
            conexion.sendall(f"✅ Listo para enviar '{nombre_archivo}' ({file_size} bytes)\n".encode('utf-8'))

            # Esperar confirmación del cliente
            respuesta = conexion.recv(1024).decode().strip()
            if respuesta.upper() != "LISTO":
                return f"❌ Cliente no está listo para recibir el archivo."

            # Enviar el archivo en chunks
            with open(ruta, 'rb') as f:
                bytes_enviados = 0
                chunk_size = 8192  # 8KB chunks
                while bytes_enviados < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    conexion.sendall(chunk)
                    bytes_enviados += len(chunk)

            # Esperar confirmación final del cliente
            try:
                confirmacion = conexion.recv(1024).decode().strip()
                if "✅" in confirmacion:
                    return f"✅ Archivo '{nombre_archivo}' enviado correctamente ({bytes_enviados} bytes)"
                else:
                    return f"⚠️ Cliente reportó un problema: {confirmacion}"
            except socket.timeout:
                return f"⚠️ No se recibió confirmación del cliente, pero el archivo podría haberse enviado correctamente."

        except socket.timeout:
            return f"❌ Error: Tiempo de espera agotado durante la transferencia."
        except ConnectionError as e:
            return f"❌ Error de conexión durante la transferencia: {e}"
        except Exception as e:
            return f"❌ Error inesperado durante la transferencia: {e}"

    except Exception as error:
        return f"❌ Error al descargar archivo: {error}"

def verificar_estado_archivo(directorio_base, nombre_archivo):
    """
    Verifica el estado de un archivo (integridad y antivirus).

    Args:
        directorio_base (str): Directorio base para operaciones con archivos
        nombre_archivo (str): Nombre del archivo a verificar

    Returns:
        str: Mensaje con el estado de verificación del archivo
    """
    try:
        # Validar nombre de archivo
        if not _es_nombre_archivo_valido(nombre_archivo):
            return "❌ Nombre de archivo inválido."

        # Construir ruta completa
        ruta = os.path.join(directorio_base, nombre_archivo)

        # Verificar si existe
        if not os.path.exists(ruta):
            return f"⚠️ Archivo '{nombre_archivo}' no encontrado."

        # Consultar estado en la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT accion, mensaje FROM log_eventos 
            WHERE accion = 'VERIFICACION' AND mensaje LIKE ? 
            ORDER BY fecha DESC LIMIT 1
        """, (f"%{nombre_archivo}%",))

        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            return f"📋 Estado de verificación para '{nombre_archivo}':\n{resultado[1]}"
        else:
            return f"ℹ️ No hay información de verificación para '{nombre_archivo}'."

    except Exception as error:
        return f"❌ Error al consultar estado: {error}"
