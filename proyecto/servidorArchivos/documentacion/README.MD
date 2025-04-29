# 🚀 Servidor de Archivos Concurrente con Acceso Remoto  

## 📌 Descripción  
Este proyecto implementa un **servidor de archivos** que permite a múltiples clientes conectarse y gestionar archivos de manera concurrente. Utiliza **sockets** para la comunicación y mecanismos de **IPC** (Inter-Process Communication) para sincronizar el acceso a los archivos. Además, emplea **asincronismo de I/O** para mejorar el rendimiento en la transferencia de datos y **cola de tareas distribuidas** para operaciones pesadas.

## 🏗️ Arquitectura del Proyecto  

El proyecto se divide en **dos componentes principales**:  

1. **🖥️ Servidor de Archivos**:  
   - Gestiona el acceso y las operaciones sobre los archivos.  
   - Se comunica con múltiples clientes de forma concurrente.  
   - Implementa mecanismos de autenticación y sincronización.  
   - Ofrece versiones síncronas y asíncronas para optimizar el rendimiento.

2. **📡 Cliente de Archivos**:  
   - Se conecta al servidor y ejecuta comandos de gestión de archivos.  
   - Permite a los usuarios listar, crear, eliminar y renombrar archivos.  
   - Soporta operaciones avanzadas como compresión y cifrado asíncrono.

---

## ⚙️ Funcionalidades  

### 📂 **Servidor**  
✔ Gestión de archivos: permite **crear, eliminar, renombrar y listar archivos**.  
✔ Acceso concurrente: maneja múltiples clientes simultáneamente.  
✔ Comunicación con clientes a través de **sockets**.  
✔ Seguridad: autenticación de usuarios para el acceso a archivos.  
✔ Procesamiento asíncrono: operaciones pesadas ejecutadas en segundo plano.
✔ Cola de tareas distribuidas: gestión eficiente de operaciones mediante Celery.
✔ Versión asíncrona: implementación con asyncio para mejor rendimiento.

### 🔌 **Cliente**  
✔ Conexión segura al servidor utilizando **sockets SSL**.  
✔ Ejecución de comandos remotos para **gestionar archivos**.  
✔ Interfaz de línea de comandos intuitiva.  
✔ Configuración mediante argumentos de línea de comandos.

---

## 🛠️ **Mecanismos de IPC y Concurrencia**  

El proyecto implementa diversas herramientas para garantizar un acceso seguro y eficiente a los archivos:  

### 🔄 **Inter-Process Communication (IPC)**  
🔹 **Sockets**: Comunicación entre el servidor y los clientes.  
🔹 **Asincronismo de I/O**: Optimización en la lectura y escritura de archivos con asyncio y aiofiles.  
🔹 **Cola de tareas**: Comunicación asíncrona mediante Celery y Redis.

### ⚡ **Sincronización y Concurrencia**  
🔹 **Threads**: Manejo de múltiples clientes en paralelo.  
🔹 **Locks**: Protección del acceso simultáneo a archivos.  
🔹 **Asyncio**: Manejo eficiente de operaciones de I/O sin bloqueo.
🔹 **Celery Workers**: Procesamiento distribuido de tareas pesadas.

---

## 📂 **Almacenamiento de Datos**  

📌 Los archivos se almacenan en el sistema de archivos local del servidor, organizados en un directorio específico.  
📌 Los datos de usuarios y logs se almacenan en una base de datos SQLite.

---

## 🎨 **Interfaz del Cliente**  

💻 El cliente utiliza una **interfaz de línea de comandos (CLI)** para enviar comandos al servidor y recibir respuestas en tiempo real.  
💻 Soporta argumentos de línea de comandos para configuración flexible.

---

## 🔑 **Principales Características**  

✅ **Servidor de archivos**: Almacena y gestiona archivos en un directorio local.  
✅ **Conexión segura**: Comunicación cifrada entre clientes y servidor.  
✅ **Acceso concurrente**: Soporte para múltiples clientes conectados simultáneamente.  
✅ **Gestión de archivos**: Operaciones básicas como **crear, eliminar, renombrar y listar archivos**.
✅ **Operaciones avanzadas**: Compresión y cifrado de archivos de forma asíncrona.
✅ **Procesamiento asíncrono**: Tareas pesadas ejecutadas en segundo plano.
✅ **Configuración flexible**: Mediante argumentos de línea de comandos.

---

## 📋 **Comandos Disponibles**

### Comandos Básicos
- `LISTAR`: Muestra los archivos disponibles en el servidor
- `CREAR <nombre>`: Crea un nuevo archivo vacío
- `ELIMINAR <nombre>`: Elimina un archivo existente
- `RENOMBRAR <viejo> <nuevo>`: Cambia el nombre de un archivo

### Comandos Avanzados
- `COMPRIMIR <nombre>`: Comprime un archivo en formato ZIP (asíncrono)
- `CIFRAR <nombre> <clave>`: Cifra un archivo con la clave proporcionada (asíncrono)
- `ESTADO <id_tarea>`: Verifica el estado de una tarea asíncrona

---

## 🚀 **Instalación y Uso**

### Requisitos
Instala las dependencias necesarias:
```bash
pip install -r requirements.txt
```

### Iniciar el Servidor
```bash
# Modo normal
python main.py -p 5000 -H 127.0.0.1 -d archivos_servidor

# Modo asíncrono
python main.py -p 5000 -H 127.0.0.1 -d archivos_servidor -a

# Modo verbose (logs detallados)
python main.py -v
```

### Iniciar el Cliente
```bash
# Conexión básica
python cliente.py -s 127.0.0.1 -p 5000

# Con usuario predefinido
python cliente.py -s 127.0.0.1 -p 5000 -u usuario1

# Modo verbose
python cliente.py -v
```

### Iniciar Workers de Celery
```bash
# Desde el directorio del proyecto
celery -A tareas.celery_app worker --loglevel=info
```
