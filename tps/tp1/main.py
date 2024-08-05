import os
from dotenv import load_dotenv
from PIL import Image
from tps.tp1.carga_division.ejercicio1 import cargar_y_dividir_imagen, guardar_partes
from tps.tp1.comunicacion_sincronizacion.ejercicio3 import procesar_imagen_con_comunicacion
from tps.tp1.manejo_senhales.ejercicio4 import manejar_senal, interrumpido
from tps.tp1.memoria_compartida.ejercicio5 import procesar_imagen_con_memoria_compartida


# Cargar las variables de entorno
load_dotenv()

# Obtener la ruta de la imagen desde las variables de entorno
ruta_imagen = os.getenv("RUTA_IMAGEN")


def combinar_imagenes(partes, ruta_salida):
    """
    Combinar partes de imágenes en una sola imagen.

    :param partes: Lista de imágenes (partes) a combinar.
    :param ruta_salida: Ruta donde se guardará la imagen combinada.
    """
    if not partes:
        raise ValueError("No hay partes de imágenes para combinar.")

    alturas = [parte.height for parte in partes]
    ancho = partes[0].width
    altura_total = sum(alturas)

    imagen_combinada = Image.new('L', (ancho, altura_total))

    y_offset = 0
    for parte in partes:
        if parte.width != ancho:
            raise ValueError("Las imágenes deben tener el mismo ancho para combinarse.")
        imagen_combinada.paste(parte, (0, y_offset))
        y_offset += parte.height

    imagen_combinada.save(ruta_salida)
    print(f'Imagen combinada guardada en: {ruta_salida}')


if __name__ == "__main__":
    import signal

    signal.signal(signal.SIGINT, manejar_senal)  # Configurar el manejador de señales

    try:
        n_partes = int(input('Ingrese el número de partes que quiera: '))

        # Dividir la imagen en partes
        partes = cargar_y_dividir_imagen(ruta_imagen, n_partes)

        # Guardar las partes y obtener las rutas guardadas
        guardar_partes(partes, 'parte_imagen')

        # Procesar la imagen utilizando comunicación entre procesos
        procesar_imagen_con_comunicacion(num_procesos=n_partes)

        if interrumpido.value:
            print("Procesamiento interrumpido. Terminando ejecución.")
        else:
            # Procesar cada parte con memoria compartida y obtener las rutas filtradas
            rutas_filtradas = []
            for i in range(n_partes):
                ruta_parte = f'parte_imagen_parte_{i + 1}.png'
                ruta_filtrada = f'{ruta_parte}_filtrada.png'
                procesar_imagen_con_memoria_compartida(ruta_parte, ruta_salida=ruta_filtrada)
                rutas_filtradas.append(ruta_filtrada)

            # Cargar las partes filtradas
            partes_filtradas = [Image.open(ruta) for ruta in rutas_filtradas]

            # Combinar las partes filtradas en una sola imagen
            ruta_imagen_combinada = 'imagen_combinada.png'
            combinar_imagenes(partes_filtradas, ruta_imagen_combinada)

    except Exception as e:
        print(f"Ocurrió un error: {e}")
