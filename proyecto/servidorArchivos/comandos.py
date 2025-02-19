import os
from baseDatos.db import registrar_log


def manejar_comando(comando, directorio_base, usuario_id):
    partes = comando.split()
    accion = partes[0].upper()

    if accion == "LISTAR":
        return listar_archivos(directorio_base, usuario_id)
    elif accion == "CREAR" and len(partes) == 2:
        return crear_archivo(directorio_base, partes[1], usuario_id)
    elif accion == "ELIMINAR" and len(partes) == 2:
        return eliminar_archivo(directorio_base, partes[1], usuario_id)
    elif accion == "RENOMBRAR" and len(partes) == 3:
        return renombrar_archivo(directorio_base, partes[1], partes[2], usuario_id)
    else:
        return "Comando no reconocido o argumentos inválidos."

def listar_archivos(directorio_base, usuario_id):
    """Lista los archivos en el directorio base"""
    archivos = os.listdir(directorio_base)
    if archivos:
        registrar_log(usuario_id, "LISTAR")
        return "\n".join(archivos)
    else:
        return "No hay archivos en el servidor."

def crear_archivo(directorio_base, nombre_archivo, usuario_id):
    """Crea un archivo vacío en el directorio base"""
    ruta = os.path.join(directorio_base, nombre_archivo)
    if not os.path.exists(ruta):
        open(ruta, 'w').close()  # Crear un archivo vacío
        registrar_log(usuario_id, "CREAR", nombre_archivo)
        return f"Archivo '{nombre_archivo}' creado."
    else:
        return f"El archivo '{nombre_archivo}' ya existe."

def eliminar_archivo(directorio_base, nombre_archivo, usuario_id):
    """Elimina un archivo en el directorio base"""
    ruta = os.path.join(directorio_base, nombre_archivo)
    if os.path.exists(ruta):
        os.remove(ruta)
        registrar_log(usuario_id, "ELIMINAR", nombre_archivo)
        return f"Archivo '{nombre_archivo}' eliminado."
    else:
        return f"Archivo '{nombre_archivo}' no encontrado."

def renombrar_archivo(directorio_base, nombre_viejo, nombre_nuevo, usuario_id):
    """Renombra un archivo en el directorio base"""
    ruta_vieja = os.path.join(directorio_base, nombre_viejo)
    ruta_nueva = os.path.join(directorio_base, nombre_nuevo)
    if os.path.exists(ruta_vieja):
        os.rename(ruta_vieja, ruta_nueva)
        registrar_log(usuario_id, "RENOMBRAR", nombre_viejo)
        return f"Archivo '{nombre_viejo}' renombrado a '{nombre_nuevo}'."
    else:
        return f"Archivo '{nombre_viejo}' no encontrado."
