# 🚀 Servidor de Archivos Concurrente con Acceso Remoto

Este proyecto implementa un **servidor de archivos concurrente** con acceso remoto usando **Python**. El servidor permite que múltiples clientes se conecten y soliciten archivos de manera concurrente, utilizando una **conexión segura (SSL/TLS)** para cifrar la comunicación entre el cliente y el servidor.

---

## 📁 Estructura del Proyecto

```bash
proyecto/
├── cliente/
│   ├── cliente.py         # Script del cliente
│   ├── Dockerfile         # Dockerfile para el cliente
├── servidor/
│   ├── servidor.py        # Script del servidor
│   ├── servidor_ssl.py    # Script del servidor con SSL
│   ├── Dockerfile         # Dockerfile para el servidor
│   ├── archivos/          # Carpeta para almacenar archivos en el servidor
│   ├── clave.pem          # Clave privada para SSL
│   ├── certificado.pem    # Certificado SSL
├── README.md              # Documentación del proyecto
├── docker-compose.yml     # Orquestación con Docker Compose
├── requirements.txt       # Dependencias del proyecto
```



## 🔒 Configuración del Servidor

1. Generar Certificados SSL

Antes de ejecutar el servidor, asegúrate de que el certificado SSL (certificado.pem) y la clave privada (clave.pem) estén presentes en el directorio servidor/.
Si no los tienes, puedes generarlos con el siguiente comando:

    openssl req -x509 -newkey rsa:4096 -keyout servidor/clave.pem -out servidor/certificado.pem -days 365 -nodes

2. Navegar al Directorio del Servidor

    ```bash
    cd proyecto/servidor
    ```
3. Ejecutar el Servidor con SSL Habilitado

    ```bash
    python servidor_ssl.py
    ```
   
## 🐳 Usando Docker con SSL

2. Construir la Imagen de Docker
    ```bash
    docker build -t servidor-archivos .
    ```
2. Ejecutar el Contenedor de Docker
    ```bash
    docker run -p 8080:8080 \
    -v $(pwd)/servidor/certificado.pem:/app/certificado.pem \
    -v $(pwd)/servidor/clave.pem:/app/clave.pem \
    servidor-archivos

    ```



## 💻 Configuración del Cliente
1. Navegar al Directorio del Cliente

    ```bash
    cd proyecto/cliente
    ```
2. Ejecutar el Cliente con conexion segura

    ```bash
   python cliente.py
    ```



## Uso

### 🔹 Servidor

El servidor escucha en 0.0.0.0:8080 y maneja las conexiones de los clientes en hilos separados.
La comunicación entre el cliente y el servidor está cifrada utilizando SSL/TLS.
Soporta los siguientes comandos:

    | Comando                  | Descripción                        |
    |--------------------------|------------------------------------|
    | `GET <nombre_archivo>`   | Descargar un archivo del servidor. |
    | `PUT <nombre_archivo>`   | Subir un archivo al servidor.      |
    | `LIST`                   | Listar todos los archivos.         |
    | `EXIT`                   | Desconectarse del servidor.        |

### 🔹 Cliente

El cliente se conecta al servidor envía comandos para interactuar con él.

    Ejemplo de descargar un archivo:
        
```bash
GET ejemplo1.txt
 ```

    Ejemplo de subir un archivo:
        
```bash
PUT ejemplo2.txt
 ```



## ⚠️ Notas Importantes

1.Asegúrate de que el directorio archivos/ exista en el servidor para almacenar y acceder a los archivos.
2.Ejecuta el servidor antes de ejecutar el cliente para establecer la conexión.
3.El servidor y el cliente deben usar los mismos certificados y claves para conectarse de forma segura.
4.El servidor utiliza SSL/TLS, por lo que el cliente debe estar configurado para conectarse a un servidor seguro.



## 🛠️ Dependencias
Las dependencias necesarias están especificadas en requirements.txt. Puedes instalarlas con el siguiente comando:

    pip install -r requirements.txt



## 🚀 Orquestación con Docker Compose
Si deseas usar Docker Compose para simplificar la ejecución del servidor y cliente, puedes hacerlo con:
        

    docker-compose up
