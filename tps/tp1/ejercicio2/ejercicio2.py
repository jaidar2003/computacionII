import numpy as np
import os
import multiprocessing as mp
from scipy.ndimage import gaussian_filter
from skimage import io, util
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

ruta_imagen = os.getenv("RUTA_IMAGEN")
ruta_carpeta_salida = os.getenv("RUTA_CARPETA_SALIDA")

def aplicar_filtro(parte_imagen, sigma=1):
    return gaussian_filter(parte_imagen, sigma=sigma)

def procesar_parte_imagen(parte_imagen, cola_resultados, sigma=1, indice=0):
    print(f"Procesando parte de la imagen {indice}...")
    parte_filtrada = aplicar_filtro(parte_imagen, sigma)
    cola_resultados.put((parte_filtrada, indice))
    print(f"Parte de la imagen {indice} procesada.")

def dividir_imagen(imagen, num_partes):
    altura = imagen.shape[0]
    altura_parte = altura // num_partes
    partes = [(imagen[i*altura_parte:(i+1)*altura_parte, :], i) for i in range(num_partes)]
    return partes

def procesamiento_paralelo_imagen(imagen, num_partes, sigma=1):
    partes = dividir_imagen(imagen, num_partes)
    cola_resultados = mp.Queue()
    procesos = []

    try:
        for parte, indice in partes:
            p = mp.Process(target=procesar_parte_imagen, args=(parte, cola_resultados, sigma, indice))
            procesos.append(p)
            p.start()

        print("Esperando la finalización de los procesos...")
        for p in procesos:
            p.join()

        print("Recuperando resultados de la cola...")
        partes_filtradas = [None] * num_partes
        while not cola_resultados.empty():
            parte_filtrada, indice = cola_resultados.get()
            partes_filtradas[indice] = parte_filtrada

        # Encontrar la forma mínima entre todas las partes filtradas
        forma_minima = min(parte_filtrada.shape for parte_filtrada in partes_filtradas)

        # Recortar todas las partes al tamaño de la parte más pequeña
        partes_recortadas = [parte_filtrada[:forma_minima[0], :forma_minima[1]] for parte_filtrada in partes_filtradas]

        print("Procesamiento en paralelo completado.")
        return np.vstack(partes_recortadas)
    except KeyboardInterrupt:
        print("Proceso interrumpido manualmente.")
        for p in procesos:
            p.terminate()
        raise


def guardar_imagenes_procesadas(imagen_procesada, ruta_carpeta_salida):
    if not os.path.exists(ruta_carpeta_salida):
        print(f"La carpeta de salida {ruta_carpeta_salida} no existe. Creando la carpeta...")
        os.makedirs(ruta_carpeta_salida)
    else:
        print(f"La carpeta de salida {ruta_carpeta_salida} ya existe.")

    for i, parte_filtrada in enumerate(imagen_procesada):
        nombre_archivo = os.path.join(ruta_carpeta_salida, f"parte_{i}.png")
        print(f"Guardando imagen procesada {i} en {nombre_archivo}")
        try:
            io.imsave(nombre_archivo, util.img_as_ubyte(parte_filtrada))
            print(f"Imagen procesada {i} guardada exitosamente.")
        except Exception as e:
            print(f"Error al guardar la imagen procesada {i}: {e}")


def main():
    imagen = io.imread(ruta_imagen, as_gray=True)
    num_partes = 4
    sigma = 2
    imagen_procesada = procesamiento_paralelo_imagen(imagen, num_partes, sigma)


    guardar_imagenes_procesadas(imagen_procesada, ruta_carpeta_salida)

    plt.figure(figsize=(10, 5))
    plt.title("Imagen Original")
    plt.imshow(imagen, cmap='gray')
    plt.show()

if __name__ == "__main__":
    main()
