# Instalación del Servidor de Archivos Concurrente

## Requisitos Previos

Antes de instalar y ejecutar el servidor de archivos, asegúrate de tener instalado:

- Python 3.7 o superior
- pip (gestor de paquetes de Python)
- Redis (para la cola de tareas distribuidas)

## Pasos de Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/computacionII.git
cd computacionII/proyecto
```

### 2. Instalar Dependencias

Instala todas las dependencias necesarias utilizando pip:

```bash
pip install -r requirements.txt
```

### 3. Configurar Certificados SSL

Para la comunicación segura, el servidor necesita certificados SSL. Puedes generar certificados autofirmados con el siguiente comando:

```bash
mkdir -p servidorArchivos/certificados
cd servidorArchivos/certificados
openssl req -x509 -newkey rsa:4096 -keyout llave.pem -out certificado.pem -days 365 -nodes
cd ../..
```

### 4. Iniciar Redis (para Celery)

Antes de iniciar el servidor con soporte para tareas distribuidas, asegúrate de que Redis esté en ejecución:

```bash
# En Linux/macOS
redis-server

# En Windows (si usas WSL o Redis para Windows)
redis-server.exe
```

### 5. Iniciar Workers de Celery

Para procesar tareas en segundo plano, inicia los workers de Celery:

```bash
cd servidorArchivos
celery -A tareas.celery_app worker --loglevel=info
```

## Ejecución del Servidor

### Modo Normal (con Threads)

```bash
python servidorArchivos/main.py -p 5000 -H 127.0.0.1 -d archivos_servidor
```

### Modo Asíncrono (con asyncio)

```bash
python servidorArchivos/main.py -p 5000 -H 127.0.0.1 -d archivos_servidor -a
```

### Modo Verbose (logs detallados)

```bash
python servidorArchivos/main.py -v
```

## Ejecución del Cliente

```bash
python servidorArchivos/cliente.py -s 127.0.0.1 -p 5000
```

## Pruebas

Para ejecutar las pruebas automatizadas:

```bash
# Pruebas del servidor normal
python test_server.py

# Pruebas del servidor asíncrono
python test_async_server.py
```

## Solución de Problemas

### Error de Conexión SSL

Si encuentras errores relacionados con SSL, verifica que los certificados se hayan generado correctamente y estén en la ubicación adecuada.

### Error de Conexión a Redis

Si Celery no puede conectarse a Redis, asegúrate de que Redis esté en ejecución y accesible en localhost:6379.

### Error de Importación de Módulos

Si encuentras errores de importación, verifica que estás ejecutando los comandos desde el directorio correcto y que todas las dependencias están instaladas.
