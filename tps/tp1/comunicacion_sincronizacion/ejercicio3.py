import sys
import os
import numpy as np
import multiprocessing
from multiprocessing import Pipe
from dotenv import load_dotenv
from PIL import Image

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from carga_division.ejercicio1 import cargar_y_dividir_imagen
from procesamiento_paralelo.ejercicio2 import aplicar_filtro, dividir_imagen

# Cargar las variables de entorno
load_dotenv()

ruta_imagen = os.getenv("RUTA_IMAGEN")

def procesar_imagen_con_comunicacion(nombre_var_env='RUTA_IMAGEN', ruta_salida='imagen_filtrada.jpg', num_procesos=4, sigma=1):
    """
    Carga una imagen desde una ruta especificada en una variable de entorno, aplica un filtro en paralelo
    con comunicación entre procesos, y guarda la imagen filtrada.

    :param nombre_var_env: Nombre de la variable de entorno que contiene la ruta de la imagen.
    :param ruta_salida: Ruta donde se guardará la imagen filtrada.
    :param num_procesos: Número de procesos a usar para el filtrado.
    :param sigma: Desviación estándar para el filtro gaussiano.
    """
    if ruta_imagen is None:
        raise ValueError(f"La variable de entorno '{nombre_var_env}' no está definida.")

    # Cargar la imagen
    imagen = Image.open(ruta_imagen).convert('L')  # Convertir a escala de grises
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
    partes_filtradas = [conn.recv() for conn in pipes]

    # Esperar a que todos los procesos terminen
    for p in procesos:
        p.join()

    # Combinar las partes filtradas
    imagen_filtrada = np.vstack(partes_filtradas)

    # Normalizar los valores de los píxeles
    imagen_filtrada = np.clip(imagen_filtrada, 0, 255)
    imagen_filtrada = (imagen_filtrada - np.min(imagen_filtrada)) / (np.max(imagen_filtrada) - np.min(imagen_filtrada)) * 255

    # Convertir a uint8 para PIL
    imagen_filtrada = imagen_filtrada.astype(np.uint8)

    # Crear y guardar la imagen filtrada
    imagen_filtrada_pil = Image.fromarray(imagen_filtrada, mode='L')
    imagen_filtrada_pil.save(ruta_salida)

def procesar_parte(parte, sigma, conn):
    """
    Aplica un filtro a una parte de la imagen y envía el resultado a través de una conexión pipe.

    :param parte: La parte de la imagen a procesar.
    :param sigma: Desviación estándar para el filtro gaussiano.
    :param conn: Conexión pipe para enviar el resultado.
    """
    parte_filtrada = aplicar_filtro(parte, sigma)
    conn.send(parte_filtrada)
    conn.close()

if __name__ == "__main__":
    procesar_imagen_con_comunicacion()
