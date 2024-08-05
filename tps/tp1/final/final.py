import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
import multiprocessing as mp
import signal
import os


# Función para cargar y dividir la imagen
def load_and_resize_image(image_path, output_size=(2, 2)):
    image = Image.open(image_path).convert('RGB')  # Convertir a RGB para asegurar tres canales
    image = image.resize(output_size, Image.LANCZOS)  # Redimensionar la imagen a 2x2
    image_array = np.array(image)
    return image_array


# Función para dividir la imagen en partes
def split_image(image_array, num_parts):
    height, width, _ = image_array.shape
    part_height = height // num_parts

    parts = []
    for i in range(num_parts):
        start_row = i * part_height
        end_row = height if i == num_parts - 1 else (i + 1) * part_height
        part = image_array[start_row:end_row, :]
        parts.append(part)

    return parts, height, width, part_height


# Función para aplicar un filtro a una parte de la imagen
def apply_filter(part, shared_array, start_index, part_shape):
    filtered_part = gaussian_filter(part, sigma=2)
    shared_array[start_index:start_index + filtered_part.size] = filtered_part.flatten()


# Función para combinar los resultados
def combine_parts(shared_array, num_parts, part_height, width, height):
    final_image_array = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(num_parts):
        start_index = i * part_height * width * 3
        part_array = np.frombuffer(shared_array.get_obj(), dtype=np.uint8, count=part_height * width * 3)
        part_array = part_array.reshape((part_height, width, 3))
        start_row = i * part_height
        end_row = start_row + part_height if i < num_parts - 1 else height
        final_image_array[start_row:end_row, :] = part_array[:end_row - start_row, :]
    return final_image_array


# Manejador de señales
def signal_handler(signum, frame):
    print(f"Proceso {os.getpid()} interrumpido")
    mp.current_process().terminate()


# Función principal
def main(image_path, num_parts):
    signal.signal(signal.SIGINT, signal_handler)

    image_array = load_and_resize_image(image_path)
    parts, height, width, part_height = split_image(image_array, num_parts)

    shared_array = mp.Array('B', height * width * 3)  # Array compartido

    processes = []
    for i, part in enumerate(parts):
        start_index = i * part_height * width * 3
        p = mp.Process(target=apply_filter, args=(part, shared_array, start_index, part.shape))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    final_image_array = combine_parts(shared_array, num_parts, part_height, width, height)
    final_image = Image.fromarray(final_image_array)
    final_image.save('final_image.png')
    print("Imagen procesada y guardada como 'final_image.png'")


if __name__ == '__main__':
    image_path = 'logo.png'
    num_parts = 2  # Número de partes en que se desea dividir la imagen
    main(image_path, num_parts)
