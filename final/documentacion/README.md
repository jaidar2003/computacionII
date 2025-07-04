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
cd computacionII
```

### 2️⃣ **Instalar dependencias**

```bash
pip install -r requirements.txt
```

Para instrucciones detalladas de instalación, incluyendo la configuración de Redis para Celery y otras opciones, consulta el archivo INSTALL.md en la carpeta de documentación.

### 3️⃣ **Generar Certificados SSL**

La creación de certificados SSL requiere dos pasos principales:

```bash
# Crear directorio para certificados
mkdir -p certificados

# 1. Generar la clave privada
openssl genrsa -out certificados/clave_privada.key 2048

# 2. Generar el certificado autofirmado
openssl req -x509 -new -nodes -key certificados/clave_privada.key -sha256 -days 365 -out certificados/certificado.pem
```

Para más detalles y opciones, consulta el archivo INSTALL.md en la carpeta de documentación.

### 4️⃣ **Ejecutar el Servidor**

```bash
python servidorArchivos/main.py
```

Para opciones adicionales:
```bash
python servidorArchivos/main.py -p 5000 -H 127.0.0.1 -d archivos -v
```

### 5️⃣ **Ejecutar el Cliente**

```bash
python servidorArchivos/cli/cliente/principal.py
```

Para opciones adicionales:
```bash
python servidorArchivos/cli/cliente/principal.py -s 127.0.0.1 -p 5000
```

### 6️⃣ **Ejecutar el Worker de Celery**

```bash
cd servidorArchivos
celery -A tareas.celery worker --loglevel=info
```

---

## 🔄 Flujo del Sistema

```
┌───────────────────┐      SSL/TLS      ┌───────────────────┐
│     Cliente       │  ◀──────────────▶ │     Servidor      │
│  (cli/cliente/)   │                   │     (main.py)     │
└───────────────────┘                   └───────────────────┘
                                                │
                                                ▼
                                     ┌────────────────────────┐
                                     │  Sistema de Archivos   │
                                     │     (archivos/)        │
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
                                     │  (historial + BD)      │
                                     └────────────────────────┘
```

---

## 📜 Comandos Disponibles

| Comando                   | Descripción                                       |
| ------------------------- | ------------------------------------------------- |
| `LISTAR`                  | Muestra los archivos en el servidor.              |
| `CREAR nombre`            | Crea un archivo vacío con el nombre especificado. |
| `SUBIR nombre`            | Sube un archivo local al servidor.                |
| `DESCARGAR nombre`        | Descarga un archivo del servidor.                 |
| `ELIMINAR nombre`         | Elimina un archivo del servidor.                  |
| `RENOMBRAR antiguo nuevo` | Cambia el nombre de un archivo.                   |
| `SALIR`                   | Cierra la conexión con el servidor.               |

---

## 🔒 Seguridad Implementada

✔️ **Autenticación de usuarios**: Verificación con credenciales antes de ejecutar comandos.
✔️ **Hashing seguro de contraseñas**: Uso de bcrypt para almacenar contraseñas de forma segura.
✔️ **SSL/TLS**: Toda la comunicación entre cliente y servidor está cifrada.
✔️ **Verificación de certificados**: Comprobación de validez y fecha de expiración de certificados SSL.
✔️ **Verificación de archivos con Celery**: integridad (hash) + escaneo antivirus (ClamAV).
✔️ **Logging de eventos**: Se registra en archivo `.log` y en tabla `log_eventos`.
✔️ **Aislamiento de usuarios**: Cada cliente tiene su propio contexto de ejecución.

---

## 📂 Estructura del Proyecto

```
final/
├── archivos/           # Directorio para almacenar archivos de usuarios
├── certificados/       # Archivos SSL (certificado.pem, clave_privada.key)
├── documentacion/      # Documentación del proyecto
│   ├── INFO.md         # Informe técnico
│   ├── INSTALL.md      # Instrucciones de instalación
│   ├── README.md       # Documentación general
│   ├── SSL.md          # Configuración de SSL
│   └── TODO.md         # Lista de mejoras futuras
├── historial/          # Archivos de registro (reemplaza historyLogs)
│   ├── cliente.log     # Registro de actividad del cliente
│   └── servidor.log    # Registro de actividad del servidor
└── servidorArchivos/
    ├── baseDeDatos/    # (antes base_datos)
    │   └── db.py       # Lógica de usuarios y logging (BD)
    ├── cli/
    │   ├── cliente/    # Subdirectorio cliente (nueva estructura)
    │   │   ├── autenticacion.py
    │   │   ├── principal.py
    │   │   ├── procesador_comandos.py
    │   │   ├── seguridad_ssl.py
    │   │   └── utilidades.py
    │   ├── ui/         # Subdirectorio UI (nueva estructura)
    │   │   ├── estilos.py      # Estilos para la interfaz de línea de comandos
    │   │   ├── interface.py    # Funciones para la interfaz de usuario
    │   │   └── mensajes.py     # Mensajes del cliente
    │   └── utils.py        # Utilidades para el cliente
    ├── server/
    │   ├── comandos/       # Subdirectorio comandos (antes era un solo archivo)
    │   │   ├── decoradores.py
    │   │   ├── manejadores.py
    │   │   ├── nucleo.py
    │   │   ├── operaciones_archivos.py
    │   │   ├── permisos.py
    │   │   └── utilidades.py
    │   ├── seguridad.py    # Módulo de autenticación y configuración SSL
    │   └── servidor.py     # Implementación del servidor
    ├── tareas/
    │   └── celery.py       # Tareas Celery (escaneo antivirus e integridad)
    ├── utils/              # Nuevo directorio de utilidades
    │   ├── config.py
    │   └── network.py
    └── main.py             # Punto de entrada principal del servidor
```

---

## 🚀 Mejoras Futuras

* [ ] Implementar una **interfaz gráfica (GUI)** para el cliente.
* [x] Soporte para **subida y descarga de archivos**.
* [ ] Integrar logging Celery en la misma base.
* [ ] Alertas automáticas si un archivo es infectado.
* [ ] Logs exportables (CSV, JSON).
* [ ] Implementar **autenticación de dos factores (2FA)** para mayor seguridad.
* [ ] Integrar con **proveedores de identidad externos** mediante OAuth/OpenID.

Para una lista completa de mejoras planificadas, consulta el archivo TODO.md en la carpeta de documentación.

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
