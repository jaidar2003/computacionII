import os
from scipy.ndimage import gaussian_filter
from PIL import Image
import numpy as np
import multiprocessing
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()


ruta_imagen = os.getenv("RUTA_IMAGEN")
def procesar_imagen_desde_env(nombre_var_env='RUTA_IMAGEN', ruta_salida='imagen_filtrada.jpg', num_procesos=4, sigma=1):
    """
    Carga una imagen desde una ruta especificada en una variable de entorno, aplica un filtro gaussiano en paralelo,
    y guarda la imagen filtrada.

    Parámetros:
    - nombre_var_env: str, nombre de la variable de entorno que contiene la ruta de la imagen.
    - ruta_salida: str, ruta donde se guardará la imagen filtrada.
    - num_procesos: int, número de procesos a usar para el filtrado.
    - sigma: float, desviación estándar para el filtro gaussiano.
    """


    if ruta_imagen is None:
        raise ValueError(f"La variable de entorno '{nombre_var_env}' no está definida.")

    # Cargar la imagen
    imagen = Image.open(ruta_imagen).convert('L')  # Convertir a escala de grises
    array_imagen = np.array(imagen)

    # Aplicar el filtro en paralelo
    imagen_filtrada = procesar_imagen_en_paralelo(array_imagen, num_procesos=num_procesos, sigma=sigma)

    # Convertir el array filtrado de nuevo a una imagen y guardarla
    imagen_filtrada_pil = Image.fromarray(imagen_filtrada)
    imagen_filtrada_pil.save(ruta_salida)

def aplicar_filtro(parte_imagen, sigma=1):
    """
    Aplica un filtro gaussiano a una parte de la imagen.

    Parámetros:
    - parte_imagen: array de numpy, la parte de la imagen a la que se le aplicará el filtro.
    - sigma: float, desviación estándar para el filtro gaussiano.

    Retorna:
    - array de numpy, la parte de la imagen filtrada.
    """
    return gaussian_filter(parte_imagen, sigma=sigma)

def dividir_imagen(imagen, num_partes):
    """
    Divide la imagen en partes iguales.

    Parámetros:
    - imagen: array de numpy, la imagen a dividir.
    - num_partes: int, el número de partes en las que se dividirá la imagen.

    Retorna:
    - lista de arrays de numpy, partes de la imagen.
    """
    altura, ancho = imagen.shape
    altura_parte = altura // num_partes
    partes = [imagen[i * altura_parte:(i + 1) * altura_parte] for i in range(num_partes)]
    return partes

def procesar_imagen_en_paralelo(imagen, num_procesos=4, sigma=1):
    """
    Aplica un filtro a la imagen en paralelo usando múltiples procesos.

    Parámetros:
    - imagen: array de numpy, la imagen completa.
    - num_procesos: int, el número de procesos a usar.
    - sigma: float, desviación estándar para el filtro gaussiano.

    Retorna:
    - array de numpy, la imagen completa filtrada.
    """
    # Dividir la imagen en partes
    partes_imagen = dividir_imagen(imagen, num_procesos)

    # Crear un pool de procesos
    with multiprocessing.Pool(processes=num_procesos) as pool:
        # Mapear la función aplicar_filtro a las partes de la imagen
        partes_filtradas = pool.starmap(aplicar_filtro, [(parte, sigma) for parte in partes_imagen])

    # Combinar las partes filtradas
    imagen_filtrada = np.vstack(partes_filtradas)

    return imagen_filtrada

if __name__ == "__main__":
    procesar_imagen_desde_env()
