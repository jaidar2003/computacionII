# Servidor de Archivos - API

Este es el componente API para el Servidor de Archivos Seguro, implementado con Flask. Actúa como un puente entre el frontend TypeScript/React y el servidor de archivos basado en sockets.

## Funcionalidad

La API proporciona endpoints RESTful que permiten al frontend interactuar con el servidor de archivos existente. Convierte las solicitudes HTTP en comandos de socket que el servidor puede entender.

## Endpoints

### Autenticación

- `GET /api/check-auth`: Verifica si el usuario está autenticado
- `POST /api/login`: Inicia sesión con nombre de usuario y contraseña
- `POST /api/register`: Registra un nuevo usuario
- `POST /api/logout`: Cierra la sesión del usuario actual

### Gestión de Archivos

- `GET /api/files`: Lista los archivos del usuario
- `POST /api/files/upload`: Sube un archivo al servidor
- `GET /api/files/download/<filename>`: Descarga un archivo específico
- `DELETE /api/files/<filename>`: Elimina un archivo específico

## Arquitectura

La API utiliza Flask para manejar las solicitudes HTTP y establece conexiones de socket con el servidor de archivos para ejecutar comandos. Cada solicitud HTTP se traduce en uno o más comandos de socket.

```
Frontend (TypeScript/React) <-> API Flask <-> Servidor de Archivos (Sockets)
```

## Requisitos

- Python 3.6 o superior
- Flask
- Flask-CORS
- El servidor de archivos debe estar en ejecución

## Ejecución

Para ejecutar solo la API:

```bash
cd final/servidorArchivos
python -m api.app
```

La API estará disponible en http://localhost:5000.

## Ejecución Completa (API + Frontend)

Para ejecutar tanto la API como el frontend juntos, puedes usar el script de desarrollo:

```bash
cd final/servidorArchivos
chmod +x run_dev.sh
./run_dev.sh
```

## Seguridad

- La API utiliza sesiones de Flask para mantener el estado de autenticación
- Las conexiones de socket al servidor de archivos utilizan SSL/TLS
- Las contraseñas nunca se almacenan en texto plano

## Desarrollo

Para añadir nuevos endpoints:

1. Define la ruta en `app.py`
2. Implementa la lógica para convertir la solicitud HTTP en comandos de socket
3. Maneja las respuestas del servidor y devuelve una respuesta HTTP apropiada

## Manejo de Errores

La API implementa un manejo de errores consistente:

- Errores de cliente (4xx): Cuando la solicitud es inválida
- Errores de servidor (5xx): Cuando hay un problema con el servidor de archivos o la API
- Todas las respuestas de error incluyen un mensaje descriptivo