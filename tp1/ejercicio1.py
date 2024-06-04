# Ejercicio 1

from PIL import Image
ruta_imagen = "/home/juanma/PycharmProjects/compu2/tp1/logo.png"

def cargar_y_dividir_imagen(ruta_imagen, n_partes):
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
def mostrar_partes(n_partes, partes):
    n_partes = int(input('ingrese el numero de partes que quiera: '))
    partes = cargar_y_dividir_imagen(ruta_imagen, n_partes)

    for i, parte in enumerate(partes):
        parte.show(title=f'Parte {i + 1}')

# Cargar la imagen desde el disco
# Obtener las dimensiones de la imagen
# Calcular la altura de cada parte
# Lista para almacenar las partes de la imagen
# Dividir la imagen en partes iguales
    # Calcular las coordenadas del área de la parte actual
    # Cortar la parte de la imagen
    # Agregar la parte a la lista
    # Mostrar las partes