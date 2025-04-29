import asyncio
import ssl
import logging
import os
from base_datos.db import registrar_log, autenticar_usuario, registrar_usuario
from hashlib import sha256

# Configurar logging
logger = logging.getLogger(__name__)

# Directorio base para archivos
DIRECTORIO_BASE = "archivos_servidor"

# Ruta de los certificados SSL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(BASE_DIR, "certificados", "certificado.pem")
KEY_PATH = os.path.join(BASE_DIR, "certificados", "llave.pem")

# Intentar importar aiofiles para operaciones de archivo asíncronas
try:
    import aiofiles
    AIOFILES_DISPONIBLE = True
    logger.info("aiofiles está disponible para operaciones de archivo asíncronas")
except ImportError:
    AIOFILES_DISPONIBLE = False
    logger.warning("aiofiles no está disponible. Se usarán operaciones síncronas.")

async def autenticar_usuario_async(username, password):
    """Autentica un usuario de forma asíncrona."""
    # Usamos asyncio.to_thread para ejecutar la función de autenticación en un hilo separado
    # ya que la operación de base de datos es bloqueante
    return await asyncio.to_thread(autenticar_usuario, username, sha256(password.encode()).hexdigest())

async def registrar_usuario_async(username, password, permisos="lectura"):
    """Registra un usuario de forma asíncrona."""
    password_hash = sha256(password.encode()).hexdigest()
    return await asyncio.to_thread(registrar_usuario, username, password_hash, permisos)

async def registrar_log_async(usuario_id, accion, archivo=None):
    """Registra una acción en los logs de forma asíncrona."""
    return await asyncio.to_thread(registrar_log, usuario_id, accion, archivo)

async def listar_archivos_async(directorio_base, usuario_id):
    """Lista los archivos en el directorio base de forma asíncrona."""
    archivos = os.listdir(directorio_base)
    if archivos:
        await registrar_log_async(usuario_id, "LISTAR")
        return "\n".join(archivos)
    else:
        return "No hay archivos en el servidor."

async def crear_archivo_async(directorio_base, nombre_archivo, usuario_id):
    """Crea un archivo vacío en el directorio base de forma asíncrona."""
    ruta = os.path.join(directorio_base, nombre_archivo)
    if not os.path.exists(ruta):
        if AIOFILES_DISPONIBLE:
            async with aiofiles.open(ruta, 'w') as f:
                pass  # Crear archivo vacío
        else:
            # Fallback a operación síncrona
            open(ruta, 'w').close()

        await registrar_log_async(usuario_id, "CREAR", nombre_archivo)
        return f"Archivo '{nombre_archivo}' creado."
    else:
        return f"El archivo '{nombre_archivo}' ya existe."

async def eliminar_archivo_async(directorio_base, nombre_archivo, usuario_id):
    """Elimina un archivo en el directorio base de forma asíncrona."""
    ruta = os.path.join(directorio_base, nombre_archivo)
    if os.path.exists(ruta):
        # Usamos asyncio.to_thread para ejecutar la operación de eliminación en un hilo separado
        await asyncio.to_thread(os.remove, ruta)
        await registrar_log_async(usuario_id, "ELIMINAR", nombre_archivo)
        return f"Archivo '{nombre_archivo}' eliminado."
    else:
        return f"Archivo '{nombre_archivo}' no encontrado."

async def renombrar_archivo_async(directorio_base, nombre_viejo, nombre_nuevo, usuario_id):
    """Renombra un archivo en el directorio base de forma asíncrona."""
    ruta_vieja = os.path.join(directorio_base, nombre_viejo)
    ruta_nueva = os.path.join(directorio_base, nombre_nuevo)
    if os.path.exists(ruta_vieja):
        # Usamos asyncio.to_thread para ejecutar la operación de renombrado en un hilo separado
        await asyncio.to_thread(os.rename, ruta_vieja, ruta_nueva)
        await registrar_log_async(usuario_id, "RENOMBRAR", nombre_viejo)
        return f"Archivo '{nombre_viejo}' renombrado a '{nombre_nuevo}'."
    else:
        return f"Archivo '{nombre_viejo}' no encontrado."

async def manejar_comando_async(comando, directorio_base, usuario_id):
    """Maneja un comando de forma asíncrona."""
    partes = comando.split()
    accion = partes[0].upper()

    if accion == "LISTAR":
        return await listar_archivos_async(directorio_base, usuario_id)
    elif accion == "CREAR" and len(partes) == 2:
        return await crear_archivo_async(directorio_base, partes[1], usuario_id)
    elif accion == "ELIMINAR" and len(partes) == 2:
        return await eliminar_archivo_async(directorio_base, partes[1], usuario_id)
    elif accion == "RENOMBRAR" and len(partes) == 3:
        return await renombrar_archivo_async(directorio_base, partes[1], partes[2], usuario_id)
    else:
        # Para comandos que usan Celery, redirigimos a la implementación síncrona
        # ya que Celery ya maneja la asincronía
        from proyecto.servidorArchivos.servidor.comandos import manejar_comando
        return manejar_comando(comando, directorio_base, usuario_id)

async def manejar_cliente_async(reader, writer, directorio_base=DIRECTORIO_BASE):
    """Maneja un cliente de forma asíncrona."""
    addr = writer.get_extra_info('peername')
    logger.info(f"🔗 Conexión aceptada desde {addr}")

    try:
        # Enviar mensaje de bienvenida
        writer.write("🌍 Bienvenido al servidor de archivos seguro asíncrono.\n".encode('utf-8'))
        await writer.drain()

        usuario_id = None
        autenticado = False

        # Bucle de autenticación
        while not autenticado:
            # Solicitar usuario
            writer.write("👤 Usuario: ".encode('utf-8'))
            await writer.drain()

            usuario_data = await reader.read(1024)
            if not usuario_data:
                break

            usuario = usuario_data.decode().strip()
            logger.info(f"📥 Usuario recibido: {usuario}")

            # Comprobar si es un comando de registro
            if usuario.upper().startswith("REGISTRAR"):
                partes = usuario.split()
                if len(partes) != 3:
                    writer.write("❌ Formato incorrecto. Usa: REGISTRAR usuario contraseña\n".encode('utf-8'))
                    await writer.drain()
                else:
                    _, nuevo_usuario, nueva_contraseña = partes
                    respuesta = await registrar_usuario_async(nuevo_usuario, nueva_contraseña)
                    writer.write(f"{respuesta}\n".encode('utf-8'))
                    await writer.drain()
                continue

            # Solicitar contraseña
            writer.write("🔒 Contraseña: ".encode('utf-8'))
            await writer.drain()

            password_data = await reader.read(1024)
            if not password_data:
                break

            password = password_data.decode().strip()
            logger.info(f"🔑 Intentando autenticar usuario {usuario}")

            # Autenticar usuario
            datos_usuario = await autenticar_usuario_async(usuario, password)
            if not datos_usuario:
                writer.write("❌ Credenciales inválidas. Intenta nuevamente.\n".encode('utf-8'))
                await writer.drain()
                continue

            usuario_id, permisos = datos_usuario
            writer.write(f"✅ Autenticación exitosa! Permisos: {permisos}\n".encode('utf-8'))
            await writer.drain()
            autenticado = True

        # Bucle de comandos
        while autenticado:
            writer.write("\n💻 Ingresar comando ('SALIR' para desconectar): ".encode('utf-8'))
            await writer.drain()

            comando_data = await reader.read(1024)
            if not comando_data:
                break

            comando = comando_data.decode().strip()
            logger.info(f"📥 Comando recibido: {comando}")

            if comando.upper() == "SALIR":
                writer.write("🔌 Desconectando...\n".encode('utf-8'))
                await writer.drain()
                break

            # Manejar comando
            respuesta = await manejar_comando_async(comando, directorio_base, usuario_id)
            writer.write(f"📄 {respuesta}\n".encode('utf-8'))
            await writer.drain()

    except Exception as e:
        logger.error(f"❌ Error con cliente {addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        logger.info(f"🔌 Conexión cerrada con {addr}")

async def iniciar_servidor_async(host='127.0.0.1', port=5000, directorio='archivos_servidor', max_intentos=5):
    """Inicia el servidor asíncrono."""
    global DIRECTORIO_BASE
    DIRECTORIO_BASE = directorio

    # Crear el directorio si no existe
    if not os.path.exists(DIRECTORIO_BASE):
        os.makedirs(DIRECTORIO_BASE)

    # Configurar SSL
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        logger.error("❌ ERROR: No se encontraron los certificados SSL.")
        return

    ssl_context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

    # Intentar iniciar el servidor con reintentos en caso de error
    intentos = 0
    puerto_actual = port

    while intentos < max_intentos:
        try:
            # Iniciar servidor
            server = await asyncio.start_server(
                lambda r, w: manejar_cliente_async(r, w, DIRECTORIO_BASE),
                host, puerto_actual, ssl=ssl_context, 
                reuse_address=True  # Equivalente a SO_REUSEADDR
            )

            addr = server.sockets[0].getsockname()
            logger.info(f'✅ Servidor asíncrono iniciado en {addr}')

            async with server:
                await server.serve_forever()

            # Si llegamos aquí, el servidor se cerró normalmente
            return

        except OSError as e:
            if e.errno == 48:  # Address already in use
                intentos += 1
                puerto_actual = port + intentos
                logger.warning(f"⚠️ Puerto {puerto_actual - 1} en uso. Intentando con puerto {puerto_actual}...")
            else:
                logger.error(f"❌ Error al iniciar el servidor: {e}")
                break

    logger.error(f"❌ No se pudo iniciar el servidor después de {max_intentos} intentos.")
    print(f"❌ No se pudo iniciar el servidor asíncrono. Todos los puertos están en uso. Intente con otro puerto usando la opción -p.")
    import sys
    sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    print("🌍 Iniciando Servidor de Archivos Asíncrono...\n")
    asyncio.run(iniciar_servidor_async())
