import os
from dotenv import load_dotenv
from PIL import Image

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la ruta de la imagen desde la variable de entorno
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


def mostrar_partes(partes):
    """
    Mostrar las partes de una imagen.

    :param partes: Una lista de partes de la imagen.
    """
    for i, parte in enumerate(partes):
        parte.show(title=f'Parte {i + 1}')


if __name__ == "__main__":
    try:
        n_partes = int(input('Ingrese el número de partes que quiera: '))
        partes = cargar_y_dividir_imagen(ruta_imagen, n_partes)
        mostrar_partes(partes)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
