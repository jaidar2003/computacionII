#!/usr/bin/env python3
"""
Script para migrar los permisos de usuarios de 'lectura' y 'escritura' a 'usuario'.

Este script actualiza la base de datos para cambiar el sistema de permisos
de tres niveles (lectura, escritura, admin) a dos niveles (usuario, admin).
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path para importar módulos del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar la función para obtener conexión a la base de datos
from baseDeDatos.db import obtener_conexion

def migrar_permisos():
    """
    Migra los permisos de 'lectura' y 'escritura' a 'usuario'.
    """
    try:
        # Obtener conexión a la base de datos
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # Contar usuarios antes de la migración
        cursor.execute("SELECT permisos, COUNT(*) FROM usuarios GROUP BY permisos")
        conteo_antes = cursor.fetchall()
        
        logger.info("Estado de permisos antes de la migración:")
        for permiso, cantidad in conteo_antes:
            logger.info(f"  - {permiso}: {cantidad} usuarios")
        
        # Actualizar permisos de 'lectura' a 'usuario'
        cursor.execute("UPDATE usuarios SET permisos = 'usuario' WHERE permisos = 'lectura'")
        lectura_actualizados = cursor.rowcount
        logger.info(f"Actualizados {lectura_actualizados} usuarios de 'lectura' a 'usuario'")
        
        # Actualizar permisos de 'escritura' a 'usuario'
        cursor.execute("UPDATE usuarios SET permisos = 'usuario' WHERE permisos = 'escritura'")
        escritura_actualizados = cursor.rowcount
        logger.info(f"Actualizados {escritura_actualizados} usuarios de 'escritura' a 'usuario'")
        
        # Contar usuarios después de la migración
        cursor.execute("SELECT permisos, COUNT(*) FROM usuarios GROUP BY permisos")
        conteo_despues = cursor.fetchall()
        
        logger.info("Estado de permisos después de la migración:")
        for permiso, cantidad in conteo_despues:
            logger.info(f"  - {permiso}: {cantidad} usuarios")
        
        # Guardar cambios
        conn.commit()
        
        # Registrar la migración en el log de eventos
        cursor.execute("""
            INSERT INTO log_eventos (usuario, ip, accion, mensaje, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "sistema", 
            "localhost", 
            "MIGRACION", 
            f"Migración de permisos: {lectura_actualizados} usuarios de 'lectura' y {escritura_actualizados} usuarios de 'escritura' actualizados a 'usuario'",
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Migración de permisos completada con éxito")
        return True
        
    except Exception as error:
        logger.error(f"❌ Error durante la migración de permisos: {error}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🔄 Iniciando migración de permisos...")
    resultado = migrar_permisos()
    
    if resultado:
        print("✅ Migración completada con éxito")
        sys.exit(0)
    else:
        print("❌ Error durante la migración")
        sys.exit(1)