# Servidor de Archivos Concurrente con Acceso Remoto

Este proyecto implementa un servidor de archivos concurrente con acceso remoto usando Python. 
El servidor permite que múltiples clientes se conecten y soliciten archivos de manera concurrente.

## Configuración del Servidor

1. **Navegar al directorio del servidor:**

    ```bash
    cd proyecto/servidor
    ```

2. **Ejecutar el servidor:**

    ```bash
    python servidor.py
    ```

3. **Usando Docker:**

    - Construir la imagen de Docker:

        ```bash
        docker build -t servidor-archivos .
        ```

    - Ejecutar el contenedor de Docker:

        ```bash
        docker run -p 8080:8080 servidor-archivos
        ```

## Configuración del Cliente

1. **Navegar al directorio del cliente:**

    ```bash
    cd proyecto/cliente
    ```

2. **Ejecutar el cliente:**

    ```bash
    python cliente.py
    ```

## Uso

- **Servidor:**
  - El servidor escucha en `0.0.0.0:8080` y maneja las conexiones de los clientes en hilos separados.
  - Soporta los siguientes comandos:
    - `GET <nombre_archivo>`: Descargar un archivo del servidor.
    - `PUT <nombre_archivo>`: Subir un archivo al servidor.
    - `LIST`: Listar todos los archivos disponibles en el servidor.
    - `EXIT`: Desconectarse del servidor.

- **Cliente:**
  - El cliente se conecta al servidor y envía comandos para interactuar con el servidor.
  - Ejemplo de comando para descargar un archivo:

    ```bash
    GET ejemplo1.txt
    ```

## Notas

- Asegúrate de que el directorio `archivos` exista en el directorio del servidor para almacenar y acceder a los archivos.
- Ejecuta el servidor antes de ejecutar el cliente para establecer una conexión.