
import os
import sys

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from baseDeDatos.db import obtener_conexion

def solicitar_cambio_permisos(usuario_id, permiso_solicitado):
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
    cursor.execute(
        "SELECT username, permisos FROM usuarios WHERE id = ?", 
        (usuario_id,)
    )
    return cursor.fetchone()

def _crear_tabla_solicitudes_si_no_existe(cursor):
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
    cursor.execute("""
        SELECT id FROM solicitudes_permisos 
        WHERE usuario_id = ? AND permiso_solicitado = ? AND estado = 'pendiente'
    """, (usuario_id, permiso_solicitado))

    return cursor.fetchone() is not None

def _registrar_solicitud(cursor, usuario_id, permiso_solicitado):
    cursor.execute("""
        INSERT INTO solicitudes_permisos (usuario_id, permiso_solicitado)
        VALUES (?, ?)
    """, (usuario_id, permiso_solicitado))

def ver_solicitudes_permisos(usuario_id):
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
    cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
    resultado = cursor.fetchone()
    return resultado[0] if resultado else None

def _obtener_solicitudes(cursor, usuario_id, es_admin):
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
    try:
        # 🔌 Obtener conexión a la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()

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
    cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
    permisos = cursor.fetchone()

    if not permisos:
        return False  # Usuario no encontrado

    return permisos[0] == 'admin'

def listar_usuarios_sistema():
    try:
        # 🔌 Obtener conexión a la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()

        # 🔍 Consultar todos los usuarios
        cursor.execute("SELECT id, username, permisos FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall()
        conn.close()

        if not usuarios:
            return "ℹ️ No hay usuarios registrados en el sistema."

        # 📋 Formatear la lista de usuarios
        resultado = "👥 Usuarios registrados en el sistema:\n"

        # Emojis para los permisos
        emojis_permiso = {
            'lectura': '📖',
            'escritura': '✏️',
            'admin': '👑'
        }

        for usuario in usuarios:
            id_usuario, username, permiso = usuario
            emoji_permiso = emojis_permiso.get(permiso, '🔑')
            resultado += f"  • ID: {id_usuario} | 👤 Usuario: {username} | {emoji_permiso} Permiso: {permiso}\n"

        # Añadir contador total
        resultado += f"\n📊 Total de usuarios: {len(usuarios)}"

        return resultado

    except Exception as error:
        return f"❌ Error al listar usuarios: {error}"

def _es_decision_valida(decision):
    return decision.lower() in ['aprobar', 'rechazar']

def _obtener_info_solicitud(cursor, id_solicitud):
    cursor.execute("""
        SELECT s.usuario_id, s.permiso_solicitado, u.username
        FROM solicitudes_permisos s
        JOIN usuarios u ON s.usuario_id = u.id
        WHERE s.id = ? AND s.estado = 'pendiente'
    """, (id_solicitud,))

    return cursor.fetchone()

def _actualizar_estado_solicitud(cursor, id_solicitud, estado):
    cursor.execute("""
        UPDATE solicitudes_permisos
        SET estado = ?, fecha_resolucion = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (estado, id_solicitud))

def _procesar_decision(cursor, decision, id_solicitud, solicitante_id, solicitante_username, permiso_solicitado):
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
