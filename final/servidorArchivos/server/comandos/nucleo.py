
import os
import sys
import socket

# Configuración básica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar decoradores desde el nuevo módulo
from .decoradores import validar_argumentos, requiere_permiso

# Importar utilidades compartidas
from comandos.utilidades import _enviar_mensaje

# Importar manejadores de comandos
from .manejadores import (
    _cmd_listar_archivos, _cmd_crear_archivo, _cmd_eliminar_archivo,
    _cmd_renombrar_archivo, _cmd_solicitar_cambio_permisos,
    _cmd_aprobar_solicitud_permisos, _cmd_ver_solicitudes_permisos,
    _cmd_verificar_archivo, _cmd_descargar_archivo, _cmd_listar_usuarios_sistema
)

# Mapeo de comandos a sus manejadores
COMANDOS = {
    "LISTAR": _cmd_listar_archivos,
    "CREAR": _cmd_crear_archivo,
    "ELIMINAR": _cmd_eliminar_archivo,
    "RENOMBRAR": _cmd_renombrar_archivo,
    "SOLICITAR_PERMISOS": _cmd_solicitar_cambio_permisos,
    "APROBAR_PERMISOS": _cmd_aprobar_solicitud_permisos,
    "VER_SOLICITUDES": _cmd_ver_solicitudes_permisos,
    "VERIFICAR": _cmd_verificar_archivo,
    "DESCARGAR": _cmd_descargar_archivo,
    "SUBIR": _cmd_crear_archivo,  # SUBIR es un alias para CREAR con contenido
    "LISTAR_USUARIOS": _cmd_listar_usuarios_sistema,  # Comando para administradores
}

def manejar_comando(comando, directorio_base, usuario_id=None, conexion=None):
    # Dividir el comando respetando las comillas
    import shlex
    try:
        partes = shlex.split(comando.strip())
    except ValueError:
        # Si hay un error al dividir (por ejemplo, comillas sin cerrar)
        # Caer en el método tradicional
        partes = comando.strip().split()

    if not partes:
        return "❌ Comando vacío."

    accion = partes[0].upper()

    # Buscar el manejador en el diccionario de comandos
    manejador = COMANDOS.get(accion)

    if manejador:
        # Pasar la conexión solo para comandos que la necesitan (DESCARGAR, SUBIR)
        if accion in ["DESCARGAR", "SUBIR"]:
            return manejador(partes, directorio_base, usuario_id, conexion)
        else:
            return manejador(partes, directorio_base, usuario_id)
    else:
        return "❌ Comando no reconocido. Usa LISTAR para ver los archivos disponibles."
