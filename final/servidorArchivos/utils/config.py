import os
import logging
import argparse
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT_PATH = os.path.join(BASE_DIR, "certificados", "certificado.pem")
KEY_PATH = os.path.join(BASE_DIR, "certificados", "llave.pem")


def crear_directorio_si_no_existe(directorio):
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        logging.info(f"📁 Directorio creado: {directorio}")
    return True

def verificar_configuracion_env():
    env_path = os.path.join(BASE_DIR, '.env')
    env_existe = os.path.exists(env_path)

    # Verificar si las variables necesarias están definidas
    servidor_host = os.getenv("SERVIDOR_HOST")
    servidor_port = os.getenv("SERVIDOR_PORT")
    db_path = os.getenv("DB_PATH")

    # Si el archivo no existe o falta alguna variable importante
    if not env_existe or not servidor_host or not servidor_port or not db_path:
        print("\n" + "="*80)
        print("⚠️  CONFIGURACIÓN INCOMPLETA DEL ARCHIVO .ENV")
        print("="*80)
        print("Se utilizarán valores predeterminados para las variables no configuradas.")
        print("\nPara personalizar la configuración, crea o edita el archivo .env con:")
        print(f"  - Ruta del archivo: {env_path}")
        print("\nEjemplo de contenido para el archivo .env:")
        print("  SERVIDOR_HOST=127.0.0.1       # Dirección IP del servidor")
        print("  SERVIDOR_PORT=1608            # Puerto del servidor")
        print("  DB_PATH=/ruta/completa/a/baseDeDatos/servidor_archivos.db")
        print("  CELERY_PATH=/ruta/a/celery    # Opcional: ruta al ejecutable de Celery")
        print("\nLos valores actuales son:")
        print(f"  SERVIDOR_HOST={os.getenv('SERVIDOR_HOST', '127.0.0.1')} (predeterminado: 127.0.0.1)")
        print(f"  SERVIDOR_PORT={os.getenv('SERVIDOR_PORT', '1608')} (predeterminado: 1608)")
        print(f"  DB_PATH={os.getenv('DB_PATH', 'baseDeDatos/servidor_archivos.db')} (predeterminado: baseDeDatos/servidor_archivos.db)")
        print("="*80 + "\n")
        return False

    return True

def configurar_argumentos(modo_dual=False):
    if modo_dual:
        # Configuración para main.py (cliente/servidor)
        parser = argparse.ArgumentParser(
            description='🔐 Cliente/Servidor de Archivos Seguro',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        parser.add_argument(
            '-m', '--modo', 
            type=str, 
            choices=['cliente', 'server'], 
            default='server',
            help='Modo de ejecución: cliente o server'
        )
    else:
        # Configuración para servidor.py (solo servidor)
        parser = argparse.ArgumentParser(
            description='🔐 Servidor de Archivos Seguro',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    # Argumentos comunes
    parser.add_argument(
        '-H', '--host', 
        type=str, 
        default=os.getenv("SERVIDOR_HOST", "127.0.0.1"),
        help='Dirección IP del servidor'
    )

    parser.add_argument(
        '-p', '--port', 
        type=int, 
        default=int(os.getenv("SERVIDOR_PORT", 1608)),
        help='Puerto del servidor'
    )

    parser.add_argument(
        '-d', '--directorio', 
        type=str, 
        default=os.getenv("SERVIDOR_DIR", "archivos"),
        help='Directorio base para archivos'
    )

    parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Mostrar logs detallados'
    )

    return parser.parse_args()
