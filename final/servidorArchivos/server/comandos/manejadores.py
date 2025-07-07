import os
import sys

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar decoradores desde el módulo de decoradores
from .decoradores import requiere_permiso, validar_argumentos

# Importar funciones de operaciones con archivos
from .operaciones_archivos import (
    listar_archivos, crear_archivo, eliminar_archivo, renombrar_archivo,
    verificar_estado_archivo, descargar_archivo, verificar_estado_todos_archivos
)

# Importar funciones de gestión de permisos
from .permisos import (
    solicitar_cambio_permisos, aprobar_cambio_permisos,
    ver_solicitudes_permisos, listar_usuarios_sistema
)

# Importar funciones de autenticación
from server.seguridad import autenticar_usuario_en_servidor, registrar_usuario

# Manejadores de comandos
@validar_argumentos(num_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: AUTH usuario contraseña")
def _cmd_autenticar_usuario(partes, directorio_base, usuario_id=None):
    usuario = partes[1]
    password = partes[2]

    datos_usuario = autenticar_usuario_en_servidor(usuario, password)
    if datos_usuario:
        usuario_id, permisos = datos_usuario
        return f"OK {usuario_id} {permisos}"
    else:
        return "ERROR Credenciales inválidas"

@validar_argumentos(num_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: REGISTER usuario contraseña")
def _cmd_registrar_usuario(partes, directorio_base, usuario_id=None):
    usuario = partes[1]
    password = partes[2]

    resultado = registrar_usuario(usuario, password)
    if resultado.startswith("✅"):
        return "OK"
    else:
        return f"ERROR {resultado}"

@requiere_permiso('lectura')
def _cmd_listar_archivos(partes, directorio_base, usuario_id=None):
    return listar_archivos(directorio_base)

@requiere_permiso('escritura')
@validar_argumentos(min_args=1, max_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: CREAR nombre_archivo [hash]")
def _cmd_crear_archivo(partes, directorio_base, usuario_id=None, conexion=None):
    # Extraer el nombre del archivo (puede contener espacios si está entre comillas)
    nombre_archivo = partes[1]

    if len(partes) == 2:
        return crear_archivo(directorio_base, nombre_archivo, None, conexion)
    else:  # len(partes) == 3
        return crear_archivo(directorio_base, nombre_archivo, partes[2], conexion)

@requiere_permiso('escritura')
@validar_argumentos(num_args=1, 
                   mensaje_error="❌ Formato incorrecto. Usa: ELIMINAR nombre_archivo")
def _cmd_eliminar_archivo(partes, directorio_base, usuario_id=None):
    # Extraer el nombre del archivo (puede contener espacios si está entre comillas)
    nombre_archivo = partes[1]
    return eliminar_archivo(directorio_base, nombre_archivo)

@requiere_permiso('escritura')
@validar_argumentos(num_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: RENOMBRAR nombre_viejo nombre_nuevo")
def _cmd_renombrar_archivo(partes, directorio_base, usuario_id=None):
    # Extraer los nombres de los archivos (pueden contener espacios si están entre comillas)
    nombre_viejo = partes[1]
    nombre_nuevo = partes[2]
    return renombrar_archivo(directorio_base, nombre_viejo, nombre_nuevo)

@requiere_permiso('lectura')
@validar_argumentos(num_args=1, 
                   mensaje_error="❌ Formato incorrecto. Usa: SOLICITAR_PERMISOS tipo_permiso")
def _cmd_solicitar_cambio_permisos(partes, directorio_base, usuario_id=None):
    return solicitar_cambio_permisos(usuario_id, partes[1])

@requiere_permiso('admin')
@validar_argumentos(num_args=2, 
                   mensaje_error="❌ Formato incorrecto. Usa: APROBAR_PERMISOS id_solicitud decision")
def _cmd_aprobar_solicitud_permisos(partes, directorio_base, usuario_id=None):
    return aprobar_cambio_permisos(usuario_id, partes[1], partes[2])

@requiere_permiso('lectura')
@validar_argumentos(num_args=0, 
                   mensaje_error="❌ Formato incorrecto. Usa: VER_SOLICITUDES")
def _cmd_ver_solicitudes_permisos(partes, directorio_base, usuario_id=None):
    return ver_solicitudes_permisos(usuario_id)

@requiere_permiso('lectura')
def _cmd_verificar_archivo(partes, directorio_base, usuario_id=None):
    # Si solo se proporciona el comando VERIFICAR sin argumentos, verificar todos los archivos
    if len(partes) == 1:
        return verificar_estado_todos_archivos(directorio_base)

    # Si se proporciona un nombre de archivo, verificar solo ese archivo
    if len(partes) == 2:
        nombre_archivo = partes[1]
        return verificar_estado_archivo(directorio_base, nombre_archivo)

    # Si hay más argumentos, mostrar mensaje de error
    return "❌ Uso: VERIFICAR [archivo]"

@requiere_permiso('lectura')
@validar_argumentos(num_args=1, 
                   mensaje_error="❌ Formato incorrecto. Usa: DESCARGAR nombre_archivo")
def _cmd_descargar_archivo(partes, directorio_base, usuario_id=None, conexion=None):
    # Extraer el nombre del archivo (puede contener espacios si está entre comillas)
    nombre_archivo = partes[1]
    return descargar_archivo(directorio_base, nombre_archivo, conexion)

@requiere_permiso('admin')
@validar_argumentos(num_args=0, 
                   mensaje_error="❌ Formato incorrecto. Usa: LISTAR_USUARIOS")
def _cmd_listar_usuarios_sistema(partes, directorio_base, usuario_id=None):
    return listar_usuarios_sistema()
