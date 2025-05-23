import os
import sys

# 🔧 Asegurar que el path raíz esté en sys.path antes de cualquier import personalizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tareas.celery import verificar_integridad_y_virus

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

# Verificar que el script se ejecuta correctamente cuando se llama directamente
if __name__ == "__main__":
    print("✅ Módulo comandos.py cargado correctamente.")
    print("✅ Importación de tareas.celery.verificar_integridad_y_virus exitosa.")
