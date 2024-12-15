# Procesamiento Paralelo de Imágenes

Este script en Python procesa imágenes en paralelo. Divide una imagen en partes, aplica un filtro de desenfoque a cada parte, y combina las partes procesadas en una imagen final.

## Requisitos

# Instala las siguientes bibliotecas:

    pip install pillow numpy scipy

### Uso

    Coloca tu imagen en el mismo directorio que el script.
    Modifica la ruta de la imagen y el número de partes (n) en el script si es necesario.
    Ejecuta el script con:



### Funciones

    cargar_imagen(ruta_imagen): Carga una imagen desde la ruta especificada.
    
    dividir_imagen(imagen, n): Divide la imagen en n partes horizontales.
    
    aplicar_filtro(parte_imagen, conexion_pipe): Aplica un filtro de desenfoque a una parte de la imagen.
    
    procesar_partes_imagen_con_pipes(partes_imagen): Procesa las partes en paralelo.
    
    guardar_partes_imagen(partes_imagen, prefijo): Guarda cada parte procesada.
    
    guardar_imagen_combinada(partes_finales, nombre_archivo_salida): Combina las partes en una imagen final.

### Ejemplo

Para procesar una imagen llamada logo.png en 4 partes, usa el siguiente código en el script:



    if __name__ == "__main__":
        ruta_imagen = 'logo.png'
        n = 4
        procesar_imagen(ruta_imagen, n)

Esto generará varias imágenes con el prefijo parte_desenfocada_ y una imagen final llamada imagen_final_combinada.png.
