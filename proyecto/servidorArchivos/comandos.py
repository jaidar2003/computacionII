import os
from ..dataBase import db

def manejar_comando(comando, directorio_base, usuario_id):
    partes = comando.split()
    accion = partes[0].upper()

    if accion == "LISTAR":
        respuesta = listar_archivos(directorio_base)
        registrar_log(usuario_id, "LISTAR")
        return respuesta

    elif accion == "CREAR" and len(partes) == 2:
        respuesta = crear_archivo(directorio_base, partes[1])
        registrar_log(usuario_id, "CREAR", partes[1])
        return respuesta

    elif accion == "ELIMINAR" and len(partes) == 2:
        respuesta = eliminar_archivo(directorio_base, partes[1])
        registrar_log(usuario_id, "ELIMINAR", partes[1])
        return respuesta

    elif accion == "RENOMBRAR" and len(partes) == 3:
        respuesta = renombrar_archivo(directorio_base, partes[1], partes[2])
        registrar_log(usuario_id, "RENOMBRAR", partes[1])
        return respuesta

    else:
        return "Comando no reconocido o argumentos inválidos."


def listar_archivos(directorio_base):
    """Lista los archivos en el directorio base"""
    archivos = os.listdir(directorio_base)
    if archivos:
        return "\n".join(archivos)
    else:
        return "No hay archivos en el servidor."


def crear_archivo(directorio_base, nombre_archivo):
    """Crea un archivo vacío en el directorio base"""
    ruta = os.path.join(directorio_base, nombre_archivo)
    if not os.path.exists(ruta):
        open(ruta, 'w').close()  # Crear un archivo vacío
        return f"Archivo '{nombre_archivo}' creado."
    else:
        return f"El archivo '{nombre_archivo}' ya existe."


def eliminar_archivo(directorio_base, nombre_archivo):
    """Elimina un archivo en el directorio base"""
    ruta = os.path.join(directorio_base, nombre_archivo)
    if os.path.exists(ruta):
        os.remove(ruta)
        return f"Archivo '{nombre_archivo}' eliminado."
    else:
        return f"Archivo '{nombre_archivo}' no encontrado."


def renombrar_archivo(directorio_base, nombre_viejo, nombre_nuevo):
    """Renombra un archivo en el directorio base"""
    ruta_vieja = os.path.join(directorio_base, nombre_viejo)
    ruta_nueva = os.path.join(directorio_base, nombre_nuevo)
    if os.path.exists(ruta_vieja):
        os.rename(ruta_vieja, ruta_nueva)
        return f"Archivo '{nombre_viejo}' renombrado a '{nombre_nuevo}'."
    else:
        return f"Archivo '{nombre_viejo}' no encontrado."
