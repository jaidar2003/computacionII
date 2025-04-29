#!/usr/bin/env python3
"""
Script para probar el servidor de archivos.
Este script inicia el servidor en modo de prueba y realiza algunas operaciones básicas.
"""

import os
import sys
import time
import logging
import threading
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
from servidorArchivos.main import iniciar_servidor_ssl

def iniciar_servidor_en_thread(host='127.0.0.1', port=5555, directorio='test_archivos'):
    """Inicia el servidor en un thread separado."""
    # Crear directorio de prueba si no existe
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    
    # Crear tablas en la base de datos
    crear_tablas()
    
    # Registrar usuario de prueba
    password_hash = sha256("test123".encode()).hexdigest()
    registrar_usuario("testuser", password_hash, "lectura,escritura")
    
    # Iniciar servidor en un thread
    server_thread = threading.Thread(
        target=iniciar_servidor_ssl,
        args=(host, port, directorio),
        daemon=True
    )
    server_thread.start()
    logger.info(f"Servidor iniciado en {host}:{port}")
    return server_thread

def probar_cliente(host='127.0.0.1', port=5555):
    """Realiza pruebas básicas como cliente."""
    try:
        # Configurar SSL
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
        
        # Conectar al servidor
        with socket.create_connection((host, port)) as sock:
            with contexto.wrap_socket(sock, server_hostname=host) as conexion_ssl:
                # Recibir mensaje de bienvenida
                bienvenida = conexion_ssl.recv(1024).decode()
                logger.info(f"Bienvenida recibida: {bienvenida}")
                
                # Iniciar sesión
                conexion_ssl.sendall(b"testuser\n")
                conexion_ssl.recv(1024)  # Prompt de contraseña
                conexion_ssl.sendall(b"test123\n")
                respuesta = conexion_ssl.recv(1024).decode()
                logger.info(f"Respuesta de autenticación: {respuesta}")
                
                if "Autenticación exitosa" not in respuesta:
                    logger.error("❌ Error en la autenticación")
                    return False
                
                # Probar comando LISTAR
                conexion_ssl.recv(1024)  # Prompt de comando
                conexion_ssl.sendall(b"LISTAR\n")
                respuesta = conexion_ssl.recv(1024).decode()
                logger.info(f"Respuesta a LISTAR: {respuesta}")
                
                # Probar comando CREAR
                conexion_ssl.recv(1024)  # Prompt de comando
                conexion_ssl.sendall(b"CREAR archivo_test.txt\n")
                respuesta = conexion_ssl.recv(1024).decode()
                logger.info(f"Respuesta a CREAR: {respuesta}")
                
                # Probar comando LISTAR de nuevo
                conexion_ssl.recv(1024)  # Prompt de comando
                conexion_ssl.sendall(b"LISTAR\n")
                respuesta = conexion_ssl.recv(1024).decode()
                logger.info(f"Respuesta a LISTAR después de CREAR: {respuesta}")
                
                # Probar comando RENOMBRAR
                conexion_ssl.recv(1024)  # Prompt de comando
                conexion_ssl.sendall(b"RENOMBRAR archivo_test.txt archivo_renombrado.txt\n")
                respuesta = conexion_ssl.recv(1024).decode()
                logger.info(f"Respuesta a RENOMBRAR: {respuesta}")
                
                # Probar comando COMPRIMIR
                conexion_ssl.recv(1024)  # Prompt de comando
                conexion_ssl.sendall(b"COMPRIMIR archivo_renombrado.txt\n")
                respuesta = conexion_ssl.recv(1024).decode()
                logger.info(f"Respuesta a COMPRIMIR: {respuesta}")
                
                # Salir
                conexion_ssl.recv(1024)  # Prompt de comando
                conexion_ssl.sendall(b"SALIR\n")
                logger.info("Pruebas completadas con éxito")
                return True
    except Exception as e:
        logger.error(f"❌ Error en las pruebas: {e}")
        return False

def main():
    """Función principal para ejecutar las pruebas."""
    parser = argparse.ArgumentParser(description='Pruebas del Servidor de Archivos')
    parser.add_argument('-p', '--port', type=int, default=5555,
                       help='Puerto para las pruebas')
    args = parser.parse_args()
    
    host = '127.0.0.1'
    port = args.port
    
    logger.info("🧪 Iniciando pruebas del servidor de archivos")
    
    # Iniciar servidor
    server_thread = iniciar_servidor_en_thread(host=host, port=port)
    
    # Esperar a que el servidor esté listo
    time.sleep(2)
    
    # Ejecutar pruebas
    resultado = probar_cliente(host=host, port=port)
    
    if resultado:
        logger.info("✅ Todas las pruebas pasaron correctamente")
    else:
        logger.error("❌ Algunas pruebas fallaron")
    
    # Mantener el servidor en ejecución por un tiempo
    time.sleep(1)
    
    logger.info("🏁 Pruebas finalizadas")

if __name__ == "__main__":
    main()