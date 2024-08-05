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

# Definir la ruta de la carpeta de destino para la imagen combinada
carpeta_destino = 'ruta/a/carpeta_destino'

# Asegurarse de que la carpeta de destino existe
if not os.path.exists(carpeta_destino):
    os.makedirs(carpeta_destino)

def combinar_imagenes_cuadricula(partes, ruta_salida):
    """
    Combina partes de imágenes en una cuadrícula 2x2.

    :param partes: Lista de imágenes (partes) a combinar.
    :param ruta_salida: Ruta donde se guardará la imagen combinada.
    """
    if len(partes) != 4:
        raise ValueError("Debe haber exactamente 4 imágenes para combinar en una cuadrícula 2x2.")

    # Asumimos que todas las imágenes tienen el mismo tamaño
    ancho, alto = partes[0].size
    ancho_total = 2 * ancho
    alto_total = 2 * alto

    imagen_combinada = Image.new('L', (ancho_total, alto_total))

    # Colocar las imágenes en la cuadrícula
    for i, parte in enumerate(partes):
        x_offset = (i % 2) * ancho
        y_offset = (i // 2) * alto
        imagen_combinada.paste(parte, (x_offset, y_offset))

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

            # Verificar que haya exactamente 4 imágenes para combinar en una cuadrícula 2x2
            if len(partes_filtradas) == 4:
                # Definir la ruta de salida para la imagen combinada
                ruta_imagen_combinada = os.path.join(carpeta_destino, 'imagen_combinada.png')

                # Combinar las partes filtradas en una cuadrícula 2x2
                combinar_imagenes_cuadricula(partes_filtradas, ruta_imagen_combinada)
            else:
                print("Se requiere exactamente 4 imágenes para combinar en una cuadrícula 2x2.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
