"""📝 Comandos del Servidor de Archivos
Implementa comandos para operaciones con archivos (LISTAR, CREAR, ELIMINAR, RENOMBRAR)
y gestión de permisos (SOLICITAR_PERMISOS, APROBAR_PERMISOS, VER_SOLICITUDES)."""

import os
import sys
import socket
from functools import wraps

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tareas.celery import verificar_integridad_y_virus
from base_datos.db import obtener_conexion

# Decorador para validar argumentos
def validar_argumentos(num_args=None, min_args=None, max_args=None, mensaje_error=None):
    """Decorador que valida el número de argumentos para un comando"""
    def decorador(func):
        @wraps(func)
        def wrapper(partes, *args, **kwargs):
            # Restar 1 para no contar el comando mismo
            num_argumentos = len(partes) - 1

            if num_args is not None and num_argumentos != num_args:
                return mensaje_error or f"❌ Este comando requiere exactamente {num_args} argumento(s)."

            if min_args is not None and num_argumentos < min_args:
                return mensaje_error or f"❌ Este comando requiere al menos {min_args} argumento(s)."

            if max_args is not None and num_argumentos > max_args:
                return mensaje_error or f"❌ Este comando permite máximo {max_args} argumento(s)."

            return func(partes, *args, **kwargs)
        return wrapper
    return decorador

# Manejadores de comandos
def _cmd_listar(partes, directorio_base, usuario_id=None):
    """Maneja comando LISTAR"""
    return listar_archivos(directorio_base)

@validar_argumentos(min_args=1, max_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: CREAR nombre_archivo [hash]")
def _cmd_crear(partes, directorio_base, usuario_id=None):
    """Maneja comando CREAR"""
    if len(partes) == 2:
        return crear_archivo(directorio_base, partes[1])
    else:  # len(partes) == 3
        return crear_archivo(directorio_base, partes[1], partes[2])

@validar_argumentos(num_args=1, 
                   mensaje_error="❌ Formato incorrecto. Usa: ELIMINAR nombre_archivo")
def _cmd_eliminar(partes, directorio_base, usuario_id=None):
    """Maneja comando ELIMINAR"""
    return eliminar_archivo(directorio_base, partes[1])

@validar_argumentos(num_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: RENOMBRAR nombre_viejo nombre_nuevo")
def _cmd_renombrar(partes, directorio_base, usuario_id=None):
    """Maneja comando RENOMBRAR"""
    return renombrar_archivo(directorio_base, partes[1], partes[2])

@validar_argumentos(num_args=1, 
                   mensaje_error="❌ Formato incorrecto. Usa: SOLICITAR_PERMISOS tipo_permiso")
def _cmd_solicitar_permisos(partes, directorio_base, usuario_id=None):
    """Maneja comando SOLICITAR_PERMISOS"""
    return solicitar_cambio_permisos(usuario_id, partes[1])

@validar_argumentos(num_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: APROBAR_PERMISOS id_solicitud decision")
def _cmd_aprobar_permisos(partes, directorio_base, usuario_id=None):
    """Maneja comando APROBAR_PERMISOS"""
    return aprobar_cambio_permisos(usuario_id, partes[1], partes[2])

@validar_argumentos(num_args=0, 
                   mensaje_error="❌ Formato incorrecto. Usa: VER_SOLICITUDES")
def _cmd_ver_solicitudes(partes, directorio_base, usuario_id=None):
    """Maneja comando VER_SOLICITUDES"""
    return ver_solicitudes_permisos(usuario_id)

# 🗺️ Mapeo de comandos a sus manejadores
def _cmd_verificar(partes, directorio_base, usuario_id=None):
    """Maneja comando VERIFICAR para comprobar estado de archivos"""
    if len(partes) != 2:
        return "❌ Uso: VERIFICAR [archivo]"

    nombre_archivo = partes[1]
    return verificar_estado_archivo(directorio_base, nombre_archivo)

COMANDOS = {
    "LISTAR": _cmd_listar,
    "CREAR": _cmd_crear,
    "ELIMINAR": _cmd_eliminar,
    "RENOMBRAR": _cmd_renombrar,
    "SOLICITAR_PERMISOS": _cmd_solicitar_permisos,
    "APROBAR_PERMISOS": _cmd_aprobar_permisos,
    "VER_SOLICITUDES": _cmd_ver_solicitudes,
    "VERIFICAR": _cmd_verificar,
}

def manejar_comando(comando, directorio_base, usuario_id=None):
    """
    🎮 Procesa un comando enviado por el usuario.

    Args:
        comando (str): Comando a ejecutar
        directorio_base (str): Directorio base para operaciones con archivos
        usuario_id (int, optional): ID del usuario que ejecuta el comando

    Returns:
        str: Resultado de la ejecución del comando
    """
    partes = comando.strip().split()
    if not partes:
        return "❌ Comando vacío."

    accion = partes[0].upper()

    # Buscar el manejador en el diccionario de comandos
    manejador = COMANDOS.get(accion)

    if manejador:
        return manejador(partes, directorio_base, usuario_id)
    else:
        return "❌ Comando no reconocido. Usa LISTAR para ver los archivos disponibles."

def listar_archivos(directorio_base):
    """
    📋 Lista todos los archivos en el directorio base.

    Args:
        directorio_base (str): Ruta al directorio donde se almacenan los archivos

    Returns:
        str: Lista de archivos o mensaje de error
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
    📝 Crea un nuevo archivo en el servidor.

    Args:
        directorio_base (str): Ruta al directorio donde se almacenan los archivos
        nombre_archivo (str): Nombre del archivo a crear
        hash_esperado (str, optional): Hash SHA-256 esperado para verificación
        conexion (ssl.SSLSocket, optional): Conexión SSL con el cliente para recibir contenido

    Returns:
        str: Mensaje de éxito o error
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
    🗑️ Elimina un archivo del servidor.

    Args:
        directorio_base (str): Ruta al directorio donde se almacenan los archivos
        nombre_archivo (str): Nombre del archivo a eliminar

    Returns:
        str: Mensaje de éxito o error
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
    ✏️ Cambia el nombre de un archivo en el servidor.

    Args:
        directorio_base (str): Ruta al directorio donde se almacenan los archivos
        nombre_viejo (str): Nombre actual del archivo
        nombre_nuevo (str): Nuevo nombre para el archivo

    Returns:
        str: Mensaje de éxito o error
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
    Verifica si un nombre de archivo es válido y seguro.

    Args:
        nombre (str): Nombre de archivo a validar

    Returns:
        bool: True si es válido, False en caso contrario
    """
    # Caracteres prohibidos en nombres de archivo
    caracteres_prohibidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(c in nombre for c in caracteres_prohibidos)

def _iniciar_verificacion(ruta, hash_esperado=None):
    """
    Inicia la verificación de integridad y antivirus en segundo plano.

    Args:
        ruta (str): Ruta completa al archivo
        hash_esperado (str, optional): Hash SHA-256 esperado para verificación
    """
    verificar_integridad_y_virus.delay(ruta, hash_esperado)

def verificar_estado_archivo(directorio_base, nombre_archivo):
    """
    🔍 Consulta el estado de verificación de un archivo.

    Args:
        directorio_base (str): Ruta al directorio donde se almacenan los archivos
        nombre_archivo (str): Nombre del archivo a verificar

    Returns:
        str: Mensaje con el estado de verificación
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

def solicitar_cambio_permisos(usuario_id, permiso_solicitado):
    """
    🔑 Registra una solicitud de cambio de permisos para un usuario.

    Args:
        usuario_id (int): ID del usuario que solicita el cambio
        permiso_solicitado (str): Permiso solicitado ('lectura', 'escritura', 'admin')

    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    # 🔍 Validar el permiso solicitado
    permisos_validos = ['lectura', 'escritura', 'admin']
    if permiso_solicitado not in permisos_validos:
        return f"❌ Permiso inválido. Opciones válidas: {', '.join(permisos_validos)}"

    try:
        # 🔌 Obtener conexión a la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()

        # 👤 Verificar si el usuario existe y obtener sus datos
        usuario_info = _obtener_info_usuario(cursor, usuario_id)
        if not usuario_info:
            conn.close()
            return "❌ Usuario no encontrado."

        username, permisos_actuales = usuario_info

        # ✅ Verificar si ya tiene el permiso solicitado
        if permisos_actuales == permiso_solicitado:
            conn.close()
            return f"ℹ️ Ya tienes el permiso '{permiso_solicitado}'."

        # 📋 Asegurar que existe la tabla de solicitudes
        _crear_tabla_solicitudes_si_no_existe(cursor)

        # 🔍 Verificar si ya existe una solicitud pendiente
        if _existe_solicitud_pendiente(cursor, usuario_id, permiso_solicitado):
            conn.close()
            return f"ℹ️ Ya tienes una solicitud pendiente para el permiso '{permiso_solicitado}'."

        # 📝 Registrar la nueva solicitud
        _registrar_solicitud(cursor, usuario_id, permiso_solicitado)

        # 💾 Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()

        return f"✅ Solicitud de permiso '{permiso_solicitado}' registrada. Un administrador la revisará pronto."

    except Exception as error:
        return f"❌ Error al solicitar cambio de permisos: {error}"

def _obtener_info_usuario(cursor, usuario_id):
    """
    👤 Obtiene información de un usuario por su ID.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        usuario_id (int): ID del usuario

    Returns:
        tuple: (username, permisos) o None si no existe
    """
    cursor.execute(
        "SELECT username, permisos FROM usuarios WHERE id = ?", 
        (usuario_id,)
    )
    return cursor.fetchone()

def _crear_tabla_solicitudes_si_no_existe(cursor):
    """
    📋 Crea la tabla de solicitudes de permisos si no existe.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_permisos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            permiso_solicitado TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_resolucion TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

def _existe_solicitud_pendiente(cursor, usuario_id, permiso_solicitado):
    """
    🔍 Verifica si ya existe una solicitud pendiente para un usuario y permiso.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        usuario_id (int): ID del usuario
        permiso_solicitado (str): Permiso solicitado

    Returns:
        bool: True si existe una solicitud pendiente, False en caso contrario
    """
    cursor.execute("""
        SELECT id FROM solicitudes_permisos 
        WHERE usuario_id = ? AND permiso_solicitado = ? AND estado = 'pendiente'
    """, (usuario_id, permiso_solicitado))

    return cursor.fetchone() is not None

def _registrar_solicitud(cursor, usuario_id, permiso_solicitado):
    """
    📝 Registra una nueva solicitud de cambio de permisos.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        usuario_id (int): ID del usuario
        permiso_solicitado (str): Permiso solicitado
    """
    cursor.execute("""
        INSERT INTO solicitudes_permisos (usuario_id, permiso_solicitado)
        VALUES (?, ?)
    """, (usuario_id, permiso_solicitado))

def ver_solicitudes_permisos(usuario_id):
    """
    📊 Muestra las solicitudes de cambio de permisos.

    Los administradores pueden ver todas las solicitudes pendientes,
    mientras que los usuarios normales solo ven sus propias solicitudes.

    Args:
        usuario_id (int): ID del usuario que solicita ver las solicitudes

    Returns:
        str: Lista de solicitudes o mensaje informativo
    """
    try:
        # 🔌 Obtener conexión a la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()

        # 👤 Verificar si el usuario existe y obtener sus permisos
        permisos_usuario = _obtener_permisos_usuario(cursor, usuario_id)
        if not permisos_usuario:
            conn.close()
            return "❌ Usuario no encontrado."

        # 🔑 Determinar si el usuario es administrador
        es_admin = permisos_usuario == 'admin'

        # 📋 Asegurar que existe la tabla de solicitudes
        _crear_tabla_solicitudes_si_no_existe(cursor)

        # 🔍 Obtener las solicitudes según el tipo de usuario
        solicitudes = _obtener_solicitudes(cursor, usuario_id, es_admin)
        conn.close()

        # 📝 Formatear y retornar el resultado
        return _formatear_resultado_solicitudes(solicitudes, es_admin)

    except Exception as error:
        return f"❌ Error al consultar solicitudes de permisos: {error}"

def _obtener_permisos_usuario(cursor, usuario_id):
    """
    🔑 Obtiene los permisos de un usuario por su ID.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        usuario_id (int): ID del usuario

    Returns:
        str: Permisos del usuario o None si no existe
    """
    cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else None

def _obtener_solicitudes(cursor, usuario_id, es_admin):
    """
    🔍 Obtiene las solicitudes de permisos según el tipo de usuario.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        usuario_id (int): ID del usuario
        es_admin (bool): Indica si el usuario es administrador

    Returns:
        list: Lista de solicitudes
    """
    if es_admin:
        # 👑 Administradores ven todas las solicitudes pendientes
        cursor.execute("""
            SELECT s.id, u.username, s.permiso_solicitado, s.fecha_solicitud
            FROM solicitudes_permisos s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.estado = 'pendiente'
            ORDER BY s.fecha_solicitud
        """)
    else:
        # 👤 Usuarios normales solo ven sus propias solicitudes
        cursor.execute("""
            SELECT s.id, u.username, s.permiso_solicitado, s.fecha_solicitud, s.estado
            FROM solicitudes_permisos s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.usuario_id = ?
            ORDER BY s.fecha_solicitud
        """, (usuario_id,))

    return cursor.fetchall()

def _formatear_resultado_solicitudes(solicitudes, es_admin):
    """
    📝 Formatea el resultado de las solicitudes para mostrar al usuario.

    Args:
        solicitudes (list): Lista de solicitudes obtenidas de la base de datos
        es_admin (bool): Indica si el usuario es administrador

    Returns:
        str: Texto formateado con las solicitudes
    """
    if not solicitudes:
        return "ℹ️ No hay solicitudes de permisos pendientes."

    resultado = "📋 Solicitudes de permisos:\n"

    # Emojis para los estados
    emojis_estado = {
        'pendiente': '⏳',
        'aprobada': '✅',
        'rechazada': '❌'
    }

    # Emojis para los permisos
    emojis_permiso = {
        'lectura': '📖',
        'escritura': '✏️',
        'admin': '👑'
    }

    for solicitud in solicitudes:
        if es_admin:
            id_solicitud, username, permiso, fecha = solicitud
            emoji_permiso = emojis_permiso.get(permiso, '🔑')
            resultado += f"  • ID: {id_solicitud} | 👤 Usuario: {username} | {emoji_permiso} Permiso: {permiso} | 📅 Fecha: {fecha}\n"
        else:
            id_solicitud, username, permiso, fecha, estado = solicitud
            emoji_permiso = emojis_permiso.get(permiso, '🔑')
            emoji_estado = emojis_estado.get(estado, '❓')
            resultado += f"  • ID: {id_solicitud} | {emoji_permiso} Permiso: {permiso} | {emoji_estado} Estado: {estado} | 📅 Fecha: {fecha}\n"

    return resultado

def aprobar_cambio_permisos(usuario_id, id_solicitud, decision):
    """
    ✅ Aprueba o rechaza una solicitud de cambio de permisos.

    Solo los administradores pueden aprobar o rechazar solicitudes.

    Args:
        usuario_id (int): ID del administrador que aprueba/rechaza
        id_solicitud (str): ID de la solicitud a aprobar/rechazar
        decision (str): 'aprobar' o 'rechazar'

    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    try:
        # 🔌 Obtener conexión a la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()

        # 👑 Verificar si el usuario es administrador
        if not _es_usuario_administrador(cursor, usuario_id):
            conn.close()
            return "❌ Solo los administradores pueden aprobar solicitudes de permisos."

        # ✓ Validar la decisión
        if not _es_decision_valida(decision):
            conn.close()
            return "❌ Decisión inválida. Opciones: 'aprobar' o 'rechazar'."

        # 🔍 Obtener información de la solicitud
        solicitud_info = _obtener_info_solicitud(cursor, id_solicitud)
        if not solicitud_info:
            conn.close()
            return f"❌ Solicitud #{id_solicitud} no encontrada o ya procesada."

        solicitante_id, permiso_solicitado, solicitante_username = solicitud_info

        # 📝 Actualizar el estado de la solicitud
        estado = 'aprobada' if decision.lower() == 'aprobar' else 'rechazada'
        _actualizar_estado_solicitud(cursor, id_solicitud, estado)

        # 🔄 Si se aprueba, actualizar los permisos del usuario
        mensaje = _procesar_decision(cursor, decision, id_solicitud, solicitante_id, 
                                    solicitante_username, permiso_solicitado)

        # 💾 Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()

        return mensaje

    except Exception as error:
        return f"❌ Error al procesar solicitud de permisos: {error}"

def _es_usuario_administrador(cursor, usuario_id):
    """
    👑 Verifica si un usuario tiene permisos de administrador.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        usuario_id (int): ID del usuario a verificar

    Returns:
        bool: True si es administrador, False en caso contrario
    """
    cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
    permisos = cursor.fetchone()

    if not permisos:
        return False  # Usuario no encontrado

    return permisos[0] == 'admin'

def _es_decision_valida(decision):
    """
    ✓ Verifica si la decisión es válida.

    Args:
        decision (str): Decisión a validar

    Returns:
        bool: True si es válida, False en caso contrario
    """
    return decision.lower() in ['aprobar', 'rechazar']

def _obtener_info_solicitud(cursor, id_solicitud):
    """
    🔍 Obtiene información de una solicitud pendiente.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        id_solicitud (str): ID de la solicitud

    Returns:
        tuple: (solicitante_id, permiso_solicitado, solicitante_username) o None
    """
    cursor.execute("""
        SELECT s.usuario_id, s.permiso_solicitado, u.username
        FROM solicitudes_permisos s
        JOIN usuarios u ON s.usuario_id = u.id
        WHERE s.id = ? AND s.estado = 'pendiente'
    """, (id_solicitud,))

    return cursor.fetchone()

def _actualizar_estado_solicitud(cursor, id_solicitud, estado):
    """
    📝 Actualiza el estado de una solicitud.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        id_solicitud (str): ID de la solicitud
        estado (str): Nuevo estado ('aprobada' o 'rechazada')
    """
    cursor.execute("""
        UPDATE solicitudes_permisos
        SET estado = ?, fecha_resolucion = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (estado, id_solicitud))

def _procesar_decision(cursor, decision, id_solicitud, solicitante_id, solicitante_username, permiso_solicitado):
    """
    🔄 Procesa la decisión tomada sobre una solicitud.

    Args:
        cursor (sqlite3.Cursor): Cursor de la base de datos
        decision (str): Decisión tomada ('aprobar' o 'rechazar')
        id_solicitud (str): ID de la solicitud
        solicitante_id (int): ID del usuario solicitante
        solicitante_username (str): Nombre de usuario del solicitante
        permiso_solicitado (str): Permiso solicitado

    Returns:
        str: Mensaje de resultado
    """
    # Emojis para los permisos
    emojis_permiso = {
        'lectura': '📖',
        'escritura': '✏️',
        'admin': '👑'
    }
    emoji_permiso = emojis_permiso.get(permiso_solicitado, '🔑')

    if decision.lower() == 'aprobar':
        # Actualizar permisos del usuario
        cursor.execute("""
            UPDATE usuarios
            SET permisos = ?
            WHERE id = ?
        """, (permiso_solicitado, solicitante_id))

        return f"✅ Solicitud #{id_solicitud} aprobada. Usuario {solicitante_username} ahora tiene permisos de {emoji_permiso} '{permiso_solicitado}'."
    else:
        return f"⛔ Solicitud #{id_solicitud} rechazada."

# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo comandos.py cargado correctamente.")
    print("✅ Importación de tareas.celery.verificar_integridad_y_virus exitosa.")
