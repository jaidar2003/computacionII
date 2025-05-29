import os
import sys

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tareas.celery import verificar_integridad_y_virus
from base_datos.db import obtener_conexion

def manejar_comando(comando, directorio_base, usuario_id=None):
    partes = comando.strip().split()
    if not partes:
        return "❌ Comando vacío."

    accion = partes[0].upper()

    if accion == "LISTAR":
        return listar_archivos(directorio_base)

    elif accion == "CREAR":
        if len(partes) == 2:
            return crear_archivo(directorio_base, partes[1])
        elif len(partes) == 3:
            return crear_archivo(directorio_base, partes[1], partes[2])
        else:
            return "❌ Formato incorrecto. Usa: CREAR nombre_archivo [hash]"

    elif accion == "ELIMINAR" and len(partes) == 2:
        return eliminar_archivo(directorio_base, partes[1])

    elif accion == "RENOMBRAR" and len(partes) == 3:
        return renombrar_archivo(directorio_base, partes[1], partes[2])

    elif accion == "SOLICITAR_PERMISOS" and len(partes) == 2:
        return solicitar_cambio_permisos(usuario_id, partes[1])

    elif accion == "APROBAR_PERMISOS" and len(partes) == 3:
        return aprobar_cambio_permisos(usuario_id, partes[1], partes[2])

    elif accion == "VER_SOLICITUDES":
        return ver_solicitudes_permisos(usuario_id)

    else:
        return "❌ Comando no reconocido o argumentos inválidos."

def listar_archivos(directorio_base):
    try:
        archivos = os.listdir(directorio_base)
        return "\n".join(archivos) if archivos else "📂 No hay archivos en el servidor."
    except Exception as e:
        return f"❌ Error al listar archivos: {e}"

def crear_archivo(directorio_base, nombre_archivo, hash_esperado=None):
    try:
        ruta = os.path.join(directorio_base, nombre_archivo)
        if not os.path.exists(ruta):
            open(ruta, 'w').close()
            # Llamar a verificación asíncrona con Celery, pasando el hash si está disponible
            verificar_integridad_y_virus.delay(ruta, hash_esperado)

            if hash_esperado:
                return f"✅ Archivo '{nombre_archivo}' creado y enviado para verificación con hash."
            else:
                return f"✅ Archivo '{nombre_archivo}' creado y enviado para verificación."
        else:
            return f"⚠️ El archivo '{nombre_archivo}' ya existe."
    except Exception as e:
        return f"❌ Error al crear archivo: {e}"

def eliminar_archivo(directorio_base, nombre_archivo):
    try:
        ruta = os.path.join(directorio_base, nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
            return f"🗑️ Archivo '{nombre_archivo}' eliminado."
        else:
            return f"⚠️ Archivo '{nombre_archivo}' no encontrado."
    except Exception as e:
        return f"❌ Error al eliminar archivo: {e}"

def renombrar_archivo(directorio_base, nombre_viejo, nombre_nuevo):
    try:
        ruta_vieja = os.path.join(directorio_base, nombre_viejo)
        ruta_nueva = os.path.join(directorio_base, nombre_nuevo)
        if os.path.exists(ruta_vieja):
            os.rename(ruta_vieja, ruta_nueva)
            return f"✏️ Archivo '{nombre_viejo}' renombrado a '{nombre_nuevo}'."
        else:
            return f"⚠️ Archivo '{nombre_viejo}' no encontrado."
    except Exception as e:
        return f"❌ Error al renombrar archivo: {e}"

def solicitar_cambio_permisos(usuario_id, permiso_solicitado):
    """
    Registra una solicitud de cambio de permisos para un usuario.

    Args:
        usuario_id (int): ID del usuario que solicita el cambio
        permiso_solicitado (str): Permiso solicitado ('lectura', 'escritura', 'admin')

    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    # Validar el permiso solicitado
    if permiso_solicitado not in ['lectura', 'escritura', 'admin']:
        return "❌ Permiso inválido. Opciones válidas: lectura, escritura, admin"

    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Verificar si el usuario existe
        cursor.execute("SELECT username, permisos FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cursor.fetchone()
        if not usuario:
            conn.close()
            return "❌ Usuario no encontrado."

        username, permisos_actuales = usuario

        # Verificar si ya tiene el permiso solicitado
        if permisos_actuales == permiso_solicitado:
            conn.close()
            return f"ℹ️ Ya tienes el permiso '{permiso_solicitado}'."

        # Verificar si ya existe una solicitud pendiente
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

        cursor.execute("""
            SELECT id FROM solicitudes_permisos 
            WHERE usuario_id = ? AND permiso_solicitado = ? AND estado = 'pendiente'
        """, (usuario_id, permiso_solicitado))

        if cursor.fetchone():
            conn.close()
            return f"ℹ️ Ya tienes una solicitud pendiente para el permiso '{permiso_solicitado}'."

        # Registrar la solicitud
        cursor.execute("""
            INSERT INTO solicitudes_permisos (usuario_id, permiso_solicitado)
            VALUES (?, ?)
        """, (usuario_id, permiso_solicitado))

        conn.commit()
        conn.close()

        return f"✅ Solicitud de permiso '{permiso_solicitado}' registrada. Un administrador la revisará pronto."

    except Exception as e:
        return f"❌ Error al solicitar cambio de permisos: {e}"

def ver_solicitudes_permisos(usuario_id):
    """
    Muestra las solicitudes de cambio de permisos pendientes.
    Solo los administradores pueden ver todas las solicitudes.

    Args:
        usuario_id (int): ID del usuario que solicita ver las solicitudes

    Returns:
        str: Lista de solicitudes pendientes o mensaje de error
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Verificar si el usuario es administrador
        cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
        permisos = cursor.fetchone()

        if not permisos:
            conn.close()
            return "❌ Usuario no encontrado."

        es_admin = permisos[0] == 'admin'

        # Crear la tabla si no existe
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

        if es_admin:
            # Administradores ven todas las solicitudes pendientes
            cursor.execute("""
                SELECT s.id, u.username, s.permiso_solicitado, s.fecha_solicitud
                FROM solicitudes_permisos s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.estado = 'pendiente'
                ORDER BY s.fecha_solicitud
            """)
        else:
            # Usuarios normales solo ven sus propias solicitudes
            cursor.execute("""
                SELECT s.id, u.username, s.permiso_solicitado, s.fecha_solicitud, s.estado
                FROM solicitudes_permisos s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.usuario_id = ?
                ORDER BY s.fecha_solicitud
            """, (usuario_id,))

        solicitudes = cursor.fetchall()
        conn.close()

        if not solicitudes:
            return "ℹ️ No hay solicitudes de permisos pendientes."

        resultado = "📋 Solicitudes de permisos:\n"
        for solicitud in solicitudes:
            if es_admin:
                id_solicitud, username, permiso, fecha = solicitud
                resultado += f"  • ID: {id_solicitud} | Usuario: {username} | Permiso: {permiso} | Fecha: {fecha}\n"
            else:
                id_solicitud, username, permiso, fecha, estado = solicitud
                resultado += f"  • ID: {id_solicitud} | Permiso: {permiso} | Estado: {estado} | Fecha: {fecha}\n"

        return resultado

    except Exception as e:
        return f"❌ Error al consultar solicitudes de permisos: {e}"

def aprobar_cambio_permisos(usuario_id, id_solicitud, decision):
    """
    Aprueba o rechaza una solicitud de cambio de permisos.
    Solo los administradores pueden aprobar solicitudes.

    Args:
        usuario_id (int): ID del administrador que aprueba/rechaza
        id_solicitud (str): ID de la solicitud a aprobar/rechazar
        decision (str): 'aprobar' o 'rechazar'

    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Verificar si el usuario es administrador
        cursor.execute("SELECT permisos FROM usuarios WHERE id = ?", (usuario_id,))
        permisos = cursor.fetchone()

        if not permisos:
            conn.close()
            return "❌ Usuario no encontrado."

        if permisos[0] != 'admin':
            conn.close()
            return "❌ Solo los administradores pueden aprobar solicitudes de permisos."

        # Validar la decisión
        if decision.lower() not in ['aprobar', 'rechazar']:
            conn.close()
            return "❌ Decisión inválida. Opciones: 'aprobar' o 'rechazar'."

        # Verificar si la solicitud existe
        cursor.execute("""
            SELECT s.usuario_id, s.permiso_solicitado, u.username
            FROM solicitudes_permisos s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.id = ? AND s.estado = 'pendiente'
        """, (id_solicitud,))

        solicitud = cursor.fetchone()
        if not solicitud:
            conn.close()
            return f"❌ Solicitud #{id_solicitud} no encontrada o ya procesada."

        solicitante_id, permiso_solicitado, solicitante_username = solicitud

        # Actualizar el estado de la solicitud
        estado = 'aprobada' if decision.lower() == 'aprobar' else 'rechazada'
        cursor.execute("""
            UPDATE solicitudes_permisos
            SET estado = ?, fecha_resolucion = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (estado, id_solicitud))

        # Si se aprueba, actualizar los permisos del usuario
        if decision.lower() == 'aprobar':
            cursor.execute("""
                UPDATE usuarios
                SET permisos = ?
                WHERE id = ?
            """, (permiso_solicitado, solicitante_id))

            mensaje = f"✅ Solicitud #{id_solicitud} aprobada. Usuario {solicitante_username} ahora tiene permisos de '{permiso_solicitado}'."
        else:
            mensaje = f"ℹ️ Solicitud #{id_solicitud} rechazada."

        conn.commit()
        conn.close()

        return mensaje

    except Exception as e:
        return f"❌ Error al procesar solicitud de permisos: {e}"

# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo comandos.py cargado correctamente.")
    print("✅ Importación de tareas.celery.verificar_integridad_y_virus exitosa.")
