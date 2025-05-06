# Servidor Seguro con Manejo de Archivos

## 📌 Introducción

Este proyecto implementa un **servidor seguro** para la gestión remota de archivos, utilizando **SSL/TLS** para cifrar la comunicación y autenticación de usuarios. Además, incluye un sistema de verificación de archivos con **Celery** para asegurar que no estén corruptos ni contengan virus, y un **sistema de registro de actividades (logging)** para auditar acciones del servidor, tanto en archivo como en base de datos.

---

## 🚀 Características Principales

✔️ **Conexiones seguras** mediante **SSL/TLS**.
✔️ **Manejo de múltiples clientes simultáneos** usando **hilos (threading)**.
✔️ **Autenticación de usuarios** antes de permitir operaciones.
✔️ **Comandos básicos para gestión de archivos** en el servidor.
✔️ **Verificación asíncrona de archivos** con Celery.
✔️ **Registro de actividad con logging en archivo y base de datos**.
✔️ **Estructura modular** para facilitar mantenimiento y escalabilidad.

---

## 🔧 Instalación y Configuración

### 1️⃣ **Clonar el repositorio**

```bash
 git clone https://github.com/jaidar2003/computacionII.git
 cd computacionII/proyecto/servidorArchivos
```

### 2️⃣ **Instalar dependencias**

```bash
pip install -r requirements.txt
```

### 3️⃣ **Generar Certificados SSL**

```bash
mkdir certificados
openssl req -x509 -newkey rsa:4096 -keyout certificados/llave.pem -out certificados/certificado.pem -days 365 -nodes
```

### 4️⃣ **Ejecutar el Servidor**

```bash
python servidor.py
```

### 5️⃣ **Ejecutar el Cliente**

```bash
python cliente.py
```

### 6️⃣ **Ejecutar el Worker de Celery**

```bash
celery -A servidor.tareas worker --loglevel=info
```

---

## 🔄 Flujo del Sistema

```
┌───────────────────┐      SSL/TLS      ┌───────────────────┐
│     Cliente       │  ◀──────────────▶ │     Servidor      │
│  (cliente.py)     │                   │  (servidor.py)    │
└───────────────────┘                   └───────────────────┘
                                                 │
                                                 ▼
                                      ┌────────────────────────┐
                                      │  Sistema de Archivos   │
                                      │  (archivos_servidor/)  │
                                      └────────────────────────┘
                                                 │
                                                 ▼
                                      ┌────────────────────────┐
                                      │ Verificación Celery    │
                                      │ (integridad y virus)   │
                                      └────────────────────────┘
                                                 │
                                                 ▼
                                      ┌────────────────────────┐
                                      │ Registro de Actividad  │
                                      │   (archivo + BD)       │
                                      └────────────────────────┘
```

---

## 📜 Comandos Disponibles

| Comando                   | Descripción                                       |
| ------------------------- | ------------------------------------------------- |
| `LISTAR`                  | Muestra los archivos en el servidor.              |
| `CREAR nombre`            | Crea un archivo vacío con el nombre especificado. |
| `ELIMINAR nombre`         | Elimina un archivo del servidor.                  |
| `RENOMBRAR antiguo nuevo` | Cambia el nombre de un archivo.                   |
| `SALIR`                   | Cierra la conexión con el servidor.               |

---

## 🔒 Seguridad Implementada

✔️ **Autenticación de usuarios**: Verificación con credenciales antes de ejecutar comandos.
✔️ **SSL/TLS**: Toda la comunicación entre cliente y servidor está cifrada.
✔️ **Verificación de archivos con Celery**: integridad (hash) + escaneo antivirus (ClamAV).
✔️ **Logging de eventos**: Se registra en archivo `.log` y en tabla `log_eventos`.
✔️ **Aislamiento de usuarios**: Cada cliente tiene su propio contexto de ejecución.

---

## 📂 Estructura del Proyecto

```
servidorArchivos/
├── cliente.py       # Cliente que se conecta al servidor
├── servidor.py      # Servidor que maneja clientes y comandos
├── comandos.py      # Funciones para gestionar archivos
├── seguridad.py     # Módulo de autenticación y configuración SSL
├── tareas.py        # Tareas Celery (escaneo antivirus e integridad)
├── main.py          # Punto de entrada principal del servidor
├── proyecto.txt     # Documentación del proyecto
├── celeryconfig.py  # Configuración de Celery
├── worker.py        # Inicializador del worker Celery
├── servidor.log     # Archivo de log para registrar actividad
├── base_datos/
│   ├── db.py        # Lógica de usuarios y logging (BD)
│   └── servidor_archivos.db
└── certificados/    # Archivos SSL (cert.pem, key.pem)
```

---

## 🚀 Mejoras Futuras

* [ ] Implementar una **interfaz gráfica (GUI)** para el cliente.
* [ ] Soporte para **subida y descarga de archivos**.
* [ ] Integrar logging Celery en la misma base.
* [ ] Alertas automáticas si un archivo es infectado.
* [ ] Logs exportables (CSV, JSON).

---

## 🏗️ Contribuciones

Haz un fork del repositorio, crea una rama con tus cambios y envía un pull request.

```bash
git checkout -b mi-mejora
# Realiza tus cambios
git commit -m "feat: Agregar nueva funcionalidad X"
git push origin mi-mejora
```

---

## 📝 Licencia

Este proyecto está bajo la licencia **MIT**. Puedes usarlo y modificarlo libremente. 😊
