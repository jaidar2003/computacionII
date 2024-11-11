# Instructivo para correr el programa

## Requisitos

- Python 3.10 o superior
- `pip` (gestor de paquetes de Python)

## Instalación de dependencias

1. Abre una terminal y navega al directorio del proyecto.
2. Instala las dependencias necesarias ejecutando el siguiente comando:

    ```sh
    pip install -r requirements.txt
    ```

## Ejecución del servidor de escalado

1. Abre una terminal y navega al directorio del proyecto.
2. Ejecuta el siguiente comando para iniciar el servidor de escalado:

    ```sh
    python tps/tp2/server-escalado.py
    ```

## Ejecución del servidor HTTP asincrónico

1. Abre una nueva terminal y navega al directorio del proyecto.
2. Ejecuta el siguiente comando para iniciar el servidor HTTP asincrónico:

    ```sh
    python tps/tp2/server-http-asincronico.py
    ```

## Envío de una imagen para procesamiento

1. Asegúrate de tener una imagen llamada `entrada.png` en el directorio del proyecto.
2. Abre una nueva terminal y navega al directorio del proyecto.
3. Ejecuta el siguiente comando para enviar la imagen al servidor HTTP para su procesamiento:

    ```sh
    python tps/tp2/main.py --input tps/tp2/imagenes/entrada.png
    ```
4. Alternativamente, puedes enviar la imagen al servidor HTTP utilizando `curl`:

    ```sh
    curl -X POST -F 'image=@/home/juanma/PycharmProjects/compu2/tps/tp2/imagenes/entrada.png' http://127.0.0.1:8080/process -o resultado.png"
    ```

5. Si el procesamiento es exitoso, la imagen procesada se guardará como `resultado.png` en el directorio del proyecto.

## Notas

- Asegúrate de que ambos servidores (escalado y HTTP) estén corriendo antes de enviar la imagen para procesamiento.
- Puedes detener los servidores presionando `CTRL+C` en la terminal correspondiente.