#!/usr/bin/env python3
"""
Script para probar el servidor de archivos asíncrono.
Este script inicia el servidor asíncrono en modo de prueba y realiza algunas operaciones básicas.
"""

import os
import sys
import time
import logging
import asyncio
import argparse
import socket
import ssl
from hashlib import sha256

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Agregar el directorio del proyecto al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar módulos del servidor
from servidorArchivos.base_datos.db import crear_tablas, registrar_usuario
from servidorArchivos.servidor_async import iniciar_servidor_async

async def iniciar_servidor_async_wrapper(host='127.0.0.1', port=5556, directorio='test_archivos_async'):
    """Inicia el servidor asíncrono."""
    # Crear directorio de prueba si no existe
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    
    # Crear tablas en la base de datos
    crear_tablas()
    
    # Registrar usuario de prueba
    password_hash = sha256("test123".encode()).hexdigest()
    registrar_usuario("testuser", password_hash, "lectura,escritura")
    
    # Iniciar servidor asíncrono
    logger.info(f"Iniciando servidor asíncrono en {host}:{port}")
    await iniciar_servidor_async(host=host, port=port, directorio=directorio)

async def probar_cliente_async(host='127.0.0.1', port=5556):
    """Realiza pruebas básicas como cliente de forma asíncrona."""
    try:
        # Configurar SSL
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
        
        # Conectar al servidor
        reader, writer = await asyncio.open_connection(
            host, port, ssl=contexto)
        
        # Recibir mensaje de bienvenida
        bienvenida = (await reader.read(1024)).decode()
        logger.info(f"Bienvenida recibida: {bienvenida}")
        
        # Iniciar sesión
        writer.write(b"testuser\n")
        await writer.drain()
        await reader.read(1024)  # Prompt de contraseña
        writer.write(b"test123\n")
        await writer.drain()
        respuesta = (await reader.read(1024)).decode()
        logger.info(f"Respuesta de autenticación: {respuesta}")
        
        if "Autenticación exitosa" not in respuesta:
            logger.error("❌ Error en la autenticación")
            writer.close()
            await writer.wait_closed()
            return False
        
        # Probar comando LISTAR
        await reader.read(1024)  # Prompt de comando
        writer.write(b"LISTAR\n")
        await writer.drain()
        respuesta = (await reader.read(1024)).decode()
        logger.info(f"Respuesta a LISTAR: {respuesta}")
        
        # Probar comando CREAR
        await reader.read(1024)  # Prompt de comando
        writer.write(b"CREAR archivo_test_async.txt\n")
        await writer.drain()
        respuesta = (await reader.read(1024)).decode()
        logger.info(f"Respuesta a CREAR: {respuesta}")
        
        # Probar comando LISTAR de nuevo
        await reader.read(1024)  # Prompt de comando
        writer.write(b"LISTAR\n")
        await writer.drain()
        respuesta = (await reader.read(1024)).decode()
        logger.info(f"Respuesta a LISTAR después de CREAR: {respuesta}")
        
        # Probar comando RENOMBRAR
        await reader.read(1024)  # Prompt de comando
        writer.write(b"RENOMBRAR archivo_test_async.txt archivo_renombrado_async.txt\n")
        await writer.drain()
        respuesta = (await reader.read(1024)).decode()
        logger.info(f"Respuesta a RENOMBRAR: {respuesta}")
        
        # Probar comando CIFRAR
        await reader.read(1024)  # Prompt de comando
        writer.write(b"CIFRAR archivo_renombrado_async.txt clave_secreta\n")
        await writer.drain()
        respuesta = (await reader.read(1024)).decode()
        logger.info(f"Respuesta a CIFRAR: {respuesta}")
        
        # Salir
        await reader.read(1024)  # Prompt de comando
        writer.write(b"SALIR\n")
        await writer.drain()
        
        # Cerrar conexión
        writer.close()
        await writer.wait_closed()
        
        logger.info("Pruebas asíncronas completadas con éxito")
        return True
    except Exception as e:
        logger.error(f"❌ Error en las pruebas asíncronas: {e}")
        return False

async def ejecutar_pruebas_async(host='127.0.0.1', port=5556):
    """Ejecuta las pruebas del servidor asíncrono."""
    # Iniciar servidor en una tarea separada
    server_task = asyncio.create_task(
        iniciar_servidor_async_wrapper(host=host, port=port)
    )
    
    # Esperar a que el servidor esté listo
    await asyncio.sleep(2)
    
    try:
        # Ejecutar pruebas
        resultado = await probar_cliente_async(host=host, port=port)
        
        if resultado:
            logger.info("✅ Todas las pruebas asíncronas pasaron correctamente")
        else:
            logger.error("❌ Algunas pruebas asíncronas fallaron")
    except Exception as e:
        logger.error(f"❌ Error durante las pruebas: {e}")
    finally:
        # Cancelar la tarea del servidor
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            logger.info("Servidor asíncrono detenido")

def main():
    """Función principal para ejecutar las pruebas."""
    parser = argparse.ArgumentParser(description='Pruebas del Servidor de Archivos Asíncrono')
    parser.add_argument('-p', '--port', type=int, default=5556,
                       help='Puerto para las pruebas')
    args = parser.parse_args()
    
    host = '127.0.0.1'
    port = args.port
    
    logger.info("🧪 Iniciando pruebas del servidor de archivos asíncrono")
    
    try:
        # Ejecutar pruebas asíncronas
        asyncio.run(ejecutar_pruebas_async(host=host, port=port))
    except KeyboardInterrupt:
        logger.info("Pruebas interrumpidas por el usuario")
    
    logger.info("🏁 Pruebas asíncronas finalizadas")

if __name__ == "__main__":
    main()