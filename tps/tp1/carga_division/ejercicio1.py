import os
from dotenv import load_dotenv
from PIL import Image

# Cargar las variables de entorno
load_dotenv()

# Obtener la ruta de la imagen desde las variables de entorno
ruta_imagen = os.getenv("RUTA_IMAGEN")

def cargar_y_dividir_imagen(ruta_imagen, n_partes):
    """
    Cargar una imagen y dividirla en partes horizontales iguales.

    :param ruta_imagen: La ruta de la imagen a cargar.
    :param n_partes: El número de partes en que se dividirá la imagen.
    :return: Una lista de partes de la imagen.
    """
    imagen = Image.open(ruta_imagen)
    ancho, alto = imagen.size
    altura_parte = alto // n_partes
    partes = []

    for i in range(n_partes):
        top = i * altura_parte
        bottom = (i + 1) * altura_parte if i < n_partes - 1 else alto
        parte = imagen.crop((0, top, ancho, bottom))
        partes.append(parte)

    return partes

def guardar_partes(partes, ruta_salida_base):
    """
    Guardar las partes de una imagen en archivos.

    :param partes: Una lista de partes de la imagen.
    :param ruta_salida_base: Ruta base para guardar las partes de la imagen.
    """
    for i, parte in enumerate(partes):
        ruta_salida = f'{ruta_salida_base}_parte_{i + 1}.png'
        parte.save(ruta_salida)
        print(f'Parte {i + 1} guardada en: {ruta_salida}')

if __name__ == "__main__":
    try:
        n_partes = int(input('Ingrese el número de partes que quiera: '))
        partes = cargar_y_dividir_imagen(ruta_imagen, n_partes)
        ruta_salida_base = 'parte_imagen'  # Ruta base para los archivos guardados
        guardar_partes(partes, ruta_salida_base)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
