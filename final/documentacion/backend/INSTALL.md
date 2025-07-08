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

Para la comunicación segura, el servidor necesita certificados SSL. La creación de certificados SSL es un proceso de múltiples pasos:

#### Método Manual (Recomendado para Entornos de Desarrollo)

```bash
# Crear directorio para certificados si no existe
mkdir -p servidorArchivos/certificados
cd servidorArchivos/certificados

# 1. Generar la clave privada
openssl genrsa -out clave_privada.key 2048

# 2. Generar el certificado autofirmado usando la clave privada
openssl req -x509 -new -nodes -key clave_privada.key -sha256 -days 365 -out certificado.pem

# Volver al directorio principal
cd ../..
```

Durante el proceso de generación del certificado, se te pedirá información como país, estado, organización, etc. Puedes completarla o simplemente presionar Enter para usar valores predeterminados.

#### Método Alternativo: Script de Automatización

También puedes crear un script bash para automatizar el proceso:

```bash
# Crear archivo crear_certificado.sh
cat > crear_certificado.sh << 'EOF'
#!/bin/bash

# Crear directorio si no existe
mkdir -p servidorArchivos/certificados

# Generar clave privada y certificado
openssl genrsa -out servidorArchivos/certificados/clave_privada.key 2048
openssl req -x509 -new -nodes -key servidorArchivos/certificados/clave_privada.key -sha256 -days 365 -out servidorArchivos/certificados/certificado.pem -subj "/C=ES/ST=Estado/L=Ciudad/O=Organización/OU=Unidad/CN=ejemplo.com"

echo "✅ Certificado y clave privada creados con éxito"
EOF

# Hacer el script ejecutable
chmod +x crear_certificado.sh

# Ejecutar el script
./crear_certificado.sh
```

Este script crea automáticamente tanto la clave privada como el certificado con valores predeterminados para los campos requeridos.

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
python servidorArchivos/main.py -p 5000 -H 127.0.0.1 -d archivos
```

### Modo Asíncrono (con asyncio)

```bash
python servidorArchivos/main.py -p 5000 -H 127.0.0.1 -d archivos -a
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
# Pruebas del server normal
python test_server.py

# Pruebas del server asíncrono
python test_async_server.py
```

## Solución de Problemas

### Error de Conexión SSL

Si encuentras errores relacionados con SSL, verifica que los certificados se hayan generado correctamente y estén en la ubicación adecuada.

### Error de Conexión a Redis

Si Celery no puede conectarse a Redis, asegúrate de que Redis esté en ejecución y accesible en localhost:6379.

### Error de Importación de Módulos

Si encuentras errores de importación, verifica que estás ejecutando los comandos desde el directorio correcto y que todas las dependencias están instaladas.
