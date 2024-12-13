from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter
import multiprocessing
import signal
import sys
import logging
# from multiprocessing import Pool
# from concurrent.futures import ProcessPoolExecutor
from numba import jit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@jit
def aplicar_filtro_optimized(array_imagen):
    return gaussian_filter(array_imagen, sigma=2)

def cargar_imagen(ruta_imagen):
    """
    Carga una imagen desde la ruta especificada.
    """
    try:
        return Image.open(ruta_imagen)
    except Exception as e:
        print(f"Error al cargar la imagen: {e}")
        sys.exit(1)


def dividir_imagen(imagen, n):
    """
    Divide la imagen en partes iguales verticalmente.

    Parámetros:
    - imagen: Imagen a dividir.
    - n: Número de partes en las que se divide la imagen.

    Retorna:
    - Una lista de partes de la imagen.
    """
    ancho, alto = imagen.size
    ancho_parte = ancho // n
    partes_imagen = []

    for i in range(n):
        izquierda = i * ancho_parte
        derecha = (i + 1) * ancho_parte if i < n - 1 else ancho
        parte = imagen.crop((izquierda, 0, derecha, alto))
        partes_imagen.append(parte)

    return partes_imagen

def aplicar_filtro(parte_imagen, conexion_pipe):
    """
    Aplica un filtro gaussiano a una parte de la imagen y envía el resultado a través del pipe.

    Parámetros:
    - parte_imagen: Parte de la imagen a procesar.
    - conexion_pipe: Conexión del pipe para enviar el resultado.
    """
    array_imagen = np.array(parte_imagen)
    array_desenfocado = gaussian_filter(array_imagen, sigma=2)
    imagen_desenfocada = Image.fromarray(array_desenfocado)
    conexion_pipe.send(np.array(imagen_desenfocada))
    conexion_pipe.close()

# def aplicar_filtro(parte_imagen):
#     """
#     Aplica un filtro gaussiano a una parte de la imagen.
#     """
#     array_imagen = np.array(parte_imagen)
#     array_desenfocado = gaussian_filter(array_imagen, sigma=2)
#     return Image.fromarray(array_desenfocado)

def procesar_partes_imagen_con_pipes(partes_imagen):
    """
    Procesa las partes de la imagen en paralelo usando pipes para la comunicación.

    Parámetros:
    - partes_imagen: Lista de partes de la imagen.

    Retorna:
    - Lista de partes de la imagen procesadas.
    """
    conexiones_padre, conexiones_hijo = zip(*[multiprocessing.Pipe() for _ in partes_imagen])
    procesos = []

    for parte, conexion_hijo in zip(partes_imagen, conexiones_hijo):
        p = multiprocessing.Process(target=aplicar_filtro, args=(parte, conexion_hijo))
        procesos.append(p)
        p.start()

    partes_procesadas = [Image.fromarray(conexion_padre.recv()) for conexion_padre in conexiones_padre]
    for p in procesos:
        p.join()

    return partes_procesadas

# def procesar_partes_imagen_con_pool(partes_imagen):
#     """
#     Procesa las partes de la imagen en paralelo usando un Pool de procesos.
#
#     Parámetros:
#     - partes_imagen: Lista de partes de la imagen.
#
#     Retorna:
#     - Lista de partes de la imagen procesadas.
#     """
#     with Pool() as pool:
#         partes_procesadas = pool.map(aplicar_filtro, partes_imagen)
#     return partes_procesadas

# def procesar_partes_imagen_con_executor(partes_imagen):
#     with ProcessPoolExecutor() as executor:
#         partes_procesadas = list(executor.map(aplicar_filtro, partes_imagen))
#     return partes_procesadas

def almacenar_parte_en_memoria_compartida(array_compartido, indice_parte, parte_imagen, ancho, alto):
    """
    Almacena una parte de la imagen en la memoria compartida.

    Parámetros:
    - array_compartido: Array compartido para almacenar las partes de la imagen.
    - indice_parte: Índice de la parte de la imagen.
    - parte_imagen: Parte de la imagen a almacenar.
    - ancho: Ancho de la imagen.
    - alto: Alto de la imagen.
    """
    array_imagen = np.array(parte_imagen)
    plano = array_imagen.flatten()
    inicio = indice_parte * ancho * alto * 3
    fin = inicio + len(plano)
    array_compartido[inicio:fin] = plano

def crear_memoria_compartida(partes_imagen):
    """
    Crea un array de memoria compartida para almacenar las partes de la imagen.

    Parámetros:
    - partes_imagen: Lista de partes de la imagen.

    Retorna:
    - Un array de memoria compartida y las dimensiones de las partes de la imagen.
    """
    ancho, alto = partes_imagen[0].size
    tamaño_total = ancho * alto * len(partes_imagen) * 3
    return multiprocessing.Array('B', tamaño_total), ancho, alto

def cargar_parte_memoria_compartida(array_compartido, indice_parte, ancho, alto):
    """
    Carga una parte de la imagen desde la memoria compartida.

    Parámetros:
    - array_compartido: Array compartido con las partes de la imagen.
    - indice_parte: Índice de la parte de la imagen.
    - ancho: Ancho de la imagen.
    - alto: Alto de la imagen.

    Retorna:
    - La parte de la imagen cargada como un objeto Image.
    """
    inicio = indice_parte * ancho * alto * 3
    fin = inicio + ancho * alto * 3
    array_imagen = np.frombuffer(array_compartido.get_obj(), dtype=np.uint8)[inicio:fin]
    return Image.fromarray(array_imagen.reshape((alto, ancho, 3)))

def usar_memoria_compartida(partes_imagen):
    """
    Utiliza la memoria compartida para almacenar y cargar partes de la imagen.

    Parámetros:
    - partes_imagen: Lista de partes de la imagen.

    Retorna:
    - Lista de partes de la imagen cargadas desde la memoria compartida.
    """
    array_compartido, ancho, alto = crear_memoria_compartida(partes_imagen)

    procesos = []
    for i, parte in enumerate(partes_imagen):
        p = multiprocessing.Process(target=almacenar_parte_en_memoria_compartida,
                                    args=(array_compartido, i, parte, ancho, alto))
        procesos.append(p)
        p.start()

    for p in procesos:
        p.join()

    partes_finales = [cargar_parte_memoria_compartida(array_compartido, i, ancho, alto) for i in
                      range(len(partes_imagen))]
    return partes_finales

def guardar_partes_imagen(partes_imagen, prefijo="parte"):
    """
    Guarda cada parte de la imagen en un archivo separado.

    Parámetros:
    - partes_imagen: Lista de partes de la imagen.
    - prefijo: Prefijo para el nombre de los archivos.
    """
    for i, parte in enumerate(partes_imagen):
        parte.save(f"{prefijo}_{i + 1}.png")
        print(f"{prefijo} {i + 1} guardado como {prefijo}_{i + 1}.png")

def guardar_imagen_combinada(partes_finales, nombre_archivo_salida="imagen_combinada.png"):
    """
    Combina las partes de la imagen en una sola imagen y la guarda en un archivo.

    Parámetros:
    - partes_finales: Lista de partes de la imagen procesadas.
    - nombre_archivo_salida: Nombre del archivo de salida.
    """
    ancho_total = sum(parte.size[0] for parte in partes_finales)
    alto = partes_finales[0].size[1]

    imagen_combinada = Image.new("RGB", (ancho_total, alto))

    desplazamiento_x = 0
    for parte in partes_finales:
        imagen_combinada.paste(parte, (desplazamiento_x, 0))
        desplazamiento_x += parte.size[0]

    imagen_combinada.save(nombre_archivo_salida)
    print(f"Imagen combinada guardada como {nombre_archivo_salida}")

def manejar_senal(sig, frame):
    """
    Manejador de señales para limpiar y salir del programa.
    """
    print('Señal recibida, limpiando...')
    sys.exit(0)

def configurar_manejo_senal():
    """
    Configura el manejo de señales para interrupciones del teclado (Ctrl+C).
    """
    signal.signal(signal.SIGINT, manejar_senal)

def procesar_imagen(ruta_imagen, n):
    """
    Procesa la imagen: la divide, aplica un filtro a cada parte, utiliza memoria compartida y guarda el resultado.

    Parámetros:
    - ruta_imagen: Ruta a la imagen que se procesará.
    - n: Número de partes en las que se dividirá la imagen.
    """
    configurar_manejo_senal()
    imagen = cargar_imagen(ruta_imagen)
    partes_imagen = dividir_imagen(imagen, n)
    partes_desenfocadas = procesar_partes_imagen_con_pipes(partes_imagen)
    guardar_partes_imagen(partes_desenfocadas, prefijo="parte_desenfocada")
    partes_finales = usar_memoria_compartida(partes_desenfocadas)
    guardar_imagen_combinada(partes_finales, nombre_archivo_salida="imagen_combinada_final.png")

if __name__ == "__main__":
    ruta_imagen = 'flag.jpeg'
    n = 4 # o n
    procesar_imagen(ruta_imagen, n)
