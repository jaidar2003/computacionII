# 🚀 Servidor de Archivos Concurrente con Acceso Remoto  

## 📌 Descripción  
Este proyecto implementa un **servidor de archivos** que permite a múltiples clientes conectarse y gestionar archivos de manera concurrente. Utiliza **sockets** para la comunicación y mecanismos de **IPC** (Inter-Process Communication) para sincronizar el acceso a los archivos. Además, emplea **asincronismo de I/O** para mejorar el rendimiento en la transferencia de datos.  

## 🏗️ Arquitectura del Proyecto  

El proyecto se divide en **dos componentes principales**:  

1. **🖥️ Servidor de Archivos**:  
   - Gestiona el acceso y las operaciones sobre los archivos.  
   - Se comunica con múltiples clientes de forma concurrente.  
   - Implementa mecanismos de autenticación y sincronización.  

2. **📡 Cliente de Archivos**:  
   - Se conecta al servidor y ejecuta comandos de gestión de archivos.  
   - Permite a los usuarios listar, crear, eliminar y renombrar archivos.  

---

## ⚙️ Funcionalidades  

### 📂 **Servidor**  
✔ Gestión de archivos: permite **crear, eliminar, renombrar y listar archivos**.  
✔ Acceso concurrente: maneja múltiples clientes simultáneamente.  
✔ Comunicación con clientes a través de **sockets**.  
✔ Seguridad: autenticación de usuarios para el acceso a archivos.  

### 🔌 **Cliente**  
✔ Conexión segura al servidor utilizando **sockets SSL**.  
✔ Ejecución de comandos remotos para **gestionar archivos**.  
✔ Interfaz de línea de comandos intuitiva.  

---

## 🛠️ **Mecanismos de IPC y Concurrencia**  

El proyecto implementa diversas herramientas para garantizar un acceso seguro y eficiente a los archivos:  

### 🔄 **Inter-Process Communication (IPC)**  
🔹 **Sockets**: Comunicación entre el servidor y los clientes.  
🔹 **Asincronismo de I/O**: Optimización en la lectura y escritura de archivos.  

### ⚡ **Sincronización y Concurrencia**  
🔹 **Threads**: Manejo de múltiples clientes en paralelo.  
🔹 **Locks**: Protección del acceso simultáneo a archivos.  

---

## 📂 **Almacenamiento de Datos**  

📌 Los archivos se almacenan en el sistema de archivos local del servidor, organizados en un directorio específico.  

---

## 🎨 **Interfaz del Cliente**  

💻 El cliente utiliza una **interfaz de línea de comandos (CLI)** para enviar comandos al servidor y recibir respuestas en tiempo real.  

---

## 🔑 **Principales Características**  

✅ **Servidor de archivos**: Almacena y gestiona archivos en un directorio local.  
✅ **Conexión segura**: Comunicación cifrada entre clientes y servidor.  
✅ **Acceso concurrente**: Soporte para múltiples clientes conectados simultáneamente.  
✅ **Gestión de archivos**: Operaciones básicas como **crear, eliminar, renombrar y listar archivos**.  
