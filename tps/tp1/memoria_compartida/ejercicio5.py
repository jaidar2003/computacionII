import os
import sys
import numpy as np
import multiprocessing
from multiprocessing import Array
from PIL import Image
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from carga_division.ejercicio1 import cargar_y_dividir_imagen
from procesamiento_paralelo.ejercicio2 import dividir_imagen, aplicar_filtro

# Cargar las variables de entorno
load_dotenv()

ruta_imagen = os.getenv("RUTA_IMAGEN")

def procesar_imagen_con_memoria_compartida(nombre_var_env='RUTA_IMAGEN', ruta_salida='imagen_filtrada.jpg', num_procesos=4, sigma=1):
    if ruta_imagen is None:
        raise ValueError(f"La variable de entorno '{nombre_var_env}' no está definida.")

    # Cargar la imagen
    imagen = Image.open(ruta_imagen)
    array_imagen = np.array(imagen)

    # Dividir la imagen en partes iguales
    partes_imagen = dividir_imagen(array_imagen, num_procesos)

    # Crear un array compartido para almacenar los resultados
    altura_parte = partes_imagen[0].shape[0]
    ancho = array_imagen.shape[1]
    memoria_compartida = Array('d', num_procesos * altura_parte * ancho)

    # Crear procesos
    procesos = []
    for i, parte in enumerate(partes_imagen):
        p = multiprocessing.Process(target=procesar_parte, args=(i, parte, sigma, memoria_compartida, altura_parte, ancho))
        procesos.append(p)
        p.start()

    # Esperar a que todos los procesos terminen
    for p in procesos:
        p.join()

    # Combinar los resultados desde la memoria compartida
    imagen_filtrada = np.empty((array_imagen.shape[0], ancho), dtype=np.float64)
    for i in range(num_procesos):
        inicio = i * altura_parte * ancho
        fin = (i + 1) * altura_parte * ancho
        imagen_filtrada[i * altura_parte:(i + 1) * altura_parte] = np.frombuffer(memoria_compartida.get_obj())[inicio:fin].reshape((altura_parte, ancho))

    # Convertir la imagen a modo 'L' (escala de grises) antes de guardarla
    imagen_filtrada_pil = Image.fromarray(np.uint8(imagen_filtrada))
    imagen_filtrada_pil = imagen_filtrada_pil.convert('L')
    imagen_filtrada_pil.save(ruta_salida)

def procesar_parte(indice, parte, sigma, memoria_compartida, altura_parte, ancho):
    parte_filtrada = aplicar_filtro(parte, sigma)
    inicio = indice * altura_parte * ancho
    fin = (indice + 1) * altura_parte * ancho
    memoria_compartida[inicio:fin] = parte_filtrada.flatten()

if __name__ == "__main__":
    procesar_imagen_con_memoria_compartida()
