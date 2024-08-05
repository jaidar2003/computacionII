import sys
import os
import signal
import multiprocessing
from multiprocessing import Pipe
from dotenv import load_dotenv
from PIL import Image
import numpy as np

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from carga_division.ejercicio1 import cargar_y_dividir_imagen
from procesamiento_paralelo.ejercicio2 import aplicar_filtro, dividir_imagen

# Cargar las variables de entorno
load_dotenv()

ruta_imagen = os.getenv("RUTA_IMAGEN")

# Flag para la interrupción
interrumpido = multiprocessing.Value('b', False)

def manejar_senal(sig, frame):
    """
    Manejador de señales para interrumpir el procesamiento de manera controlada.
    """
    print("Interrupción detectada. Terminando procesos...")
    interrumpido.value = True

# Configurar el manejador de señales
signal.signal(signal.SIGINT, manejar_senal)

def procesar_imagen_con_comunicacion(nombre_var_env='RUTA_IMAGEN', ruta_salida='imagen_filtrada.jpg', num_procesos=4, sigma=1):
    """
    Carga una imagen desde una ruta especificada en una variable de entorno, aplica un filtro en paralelo
    con comunicación entre procesos, y guarda la imagen filtrada.
    """
    if ruta_imagen is None:
        raise ValueError(f"La variable de entorno '{nombre_var_env}' no está definida.")

    # Cargar la imagen
    imagen = Image.open(ruta_imagen)
    array_imagen = np.array(imagen)

    # Dividir la imagen en partes iguales
    partes_imagen = dividir_imagen(array_imagen, num_procesos)

    # Crear pipes y procesos
    procesos = []
    pipes = []

    for parte in partes_imagen:
        parent_conn, child_conn = Pipe()
        pipes.append(parent_conn)
        p = multiprocessing.Process(target=procesar_parte, args=(parte, sigma, child_conn))
        procesos.append(p)
        p.start()

    # Recibir las partes filtradas
    partes_filtradas = []
    for conn in pipes:
        if interrumpido.value:
            break
        partes_filtradas.append(conn.recv())

    # Esperar a que todos los procesos terminen
    for p in procesos:
        p.join()

    if interrumpido.value:
        print("Proceso interrumpido. Guardando imagen parcial.")
    else:
        # Asegurarse de que las partes filtradas están correctamente combinadas
        imagen_filtrada = np.vstack(partes_filtradas)

        # Convertir a 'RGB' o 'L' según el modo de la imagen original
        imagen_original = Image.open(ruta_imagen)
        modo_imagen = imagen_original.mode
        if modo_imagen == 'RGB':
            imagen_filtrada_pil = Image.fromarray(imagen_filtrada.astype(np.uint8), mode='RGB')
        else:
            imagen_filtrada_pil = Image.fromarray(imagen_filtrada.astype(np.uint8), mode='L')

        # Guardar la imagen filtrada
        imagen_filtrada_pil.save(ruta_salida)

def procesar_parte(parte, sigma, conn):
    """
    Aplica un filtro a una parte de la imagen y envía el resultado a través de una conexión pipe.
    """
    if interrumpido.value:
        return
    parte_filtrada = aplicar_filtro(parte, sigma)
    conn.send(parte_filtrada)
    conn.close()

if __name__ == "__main__":
    procesar_imagen_con_comunicacion()
