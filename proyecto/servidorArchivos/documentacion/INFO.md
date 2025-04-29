# Informe Técnico: Servidor de Archivos Concurrente

## Decisiones de Diseño

### 1. Arquitectura Cliente-Servidor

Se eligió una arquitectura cliente-servidor tradicional con comunicación mediante sockets TCP/IP por las siguientes razones:

- **Robustez**: Los sockets TCP proporcionan una comunicación confiable y orientada a la conexión.
- **Flexibilidad**: Permite implementar un protocolo de comunicación personalizado.
- **Seguridad**: Facilita la implementación de SSL/TLS para cifrar las comunicaciones.

### 2. Concurrencia con Threads vs. Procesos

Se optó por utilizar threads para manejar múltiples clientes en lugar de procesos por:

- **Eficiencia de recursos**: Los threads comparten el mismo espacio de memoria, lo que reduce la sobrecarga.
- **Comunicación simplificada**: No se requieren mecanismos de IPC complejos entre threads.
- **Naturaleza de las operaciones**: Las operaciones de I/O son bloqueantes, lo que hace que los threads sean adecuados ya que pueden esperar eficientemente mientras se completan las operaciones de I/O.

### 3. Implementación Asíncrona con asyncio

Se implementó una versión asíncrona del servidor utilizando asyncio por:

- **Escalabilidad**: Permite manejar miles de conexiones simultáneas con recursos limitados.
- **Eficiencia**: Evita el bloqueo durante operaciones de I/O, mejorando el rendimiento general.
- **Modelo de programación moderno**: Facilita el razonamiento sobre operaciones concurrentes con un código más limpio y mantenible.

### 4. Cola de Tareas Distribuidas con Celery

Se eligió Celery con Redis como broker para implementar la cola de tareas distribuidas por:

- **Escalabilidad**: Permite distribuir tareas entre múltiples workers.
- **Fiabilidad**: Garantiza que las tareas se completen incluso si hay fallos.
- **Monitoreo**: Proporciona herramientas para supervisar el estado de las tareas.
- **Flexibilidad**: Permite programar tareas para ejecución futura o periódica.

### 5. Almacenamiento de Datos

#### Sistema de Archivos para Archivos de Usuario

Los archivos de los usuarios se almacenan en el sistema de archivos local por:

- **Simplicidad**: Aprovecha las capacidades del sistema operativo para gestionar archivos.
- **Rendimiento**: Acceso directo a los archivos sin capas intermedias.
- **Compatibilidad**: Funciona con cualquier tipo de archivo sin necesidad de conversión.

#### SQLite para Datos de Usuario y Logs

Se utilizó SQLite para almacenar información de usuarios y registros de actividad por:

- **Simplicidad**: No requiere un servidor de base de datos separado.
- **Portabilidad**: La base de datos es un único archivo que se puede mover fácilmente.
- **Transacciones ACID**: Garantiza la integridad de los datos incluso en caso de fallos.

### 6. Seguridad

#### SSL/TLS para Comunicaciones

Se implementó SSL/TLS para cifrar las comunicaciones entre cliente y servidor por:

- **Confidencialidad**: Protege los datos transmitidos de ser interceptados.
- **Integridad**: Garantiza que los datos no sean alterados durante la transmisión.
- **Autenticación**: Verifica la identidad del servidor.

#### Hashing de Contraseñas

Se utilizó SHA-256 para almacenar las contraseñas de los usuarios por:

- **Seguridad**: Evita almacenar contraseñas en texto plano.
- **Rendimiento**: Ofrece un buen equilibrio entre seguridad y velocidad.

### 7. Interfaz de Línea de Comandos

Se implementó una interfaz de línea de comandos (CLI) tanto para el cliente como para el servidor por:

- **Simplicidad**: Facilita la automatización y el uso en scripts.
- **Flexibilidad**: Permite configurar el comportamiento mediante argumentos.
- **Accesibilidad**: Funciona en entornos sin interfaz gráfica.

## Justificación de Herramientas y Tecnologías

### Python como Lenguaje Principal

Se eligió Python por:

- **Legibilidad**: Código claro y fácil de entender.
- **Bibliotecas**: Amplio ecosistema de bibliotecas para redes, concurrencia, etc.
- **Portabilidad**: Funciona en múltiples plataformas sin cambios.
- **Desarrollo rápido**: Permite implementar funcionalidades complejas con menos código.

### asyncio para Operaciones Asíncronas

Se utilizó asyncio por:

- **Estándar de la biblioteca**: Forma parte de la biblioteca estándar de Python.
- **Modelo de programación coherente**: Proporciona un modelo mental claro para la programación asíncrona.
- **Interoperabilidad**: Se integra bien con otras bibliotecas asíncronas.

### Celery para Tareas Distribuidas

Se eligió Celery por:

- **Madurez**: Proyecto estable y ampliamente utilizado.
- **Flexibilidad**: Soporta múltiples brokers (Redis, RabbitMQ, etc.).
- **Funcionalidades avanzadas**: Reintentos, programación, prioridades, etc.

### Redis como Broker de Mensajes

Se utilizó Redis por:

- **Rendimiento**: Alta velocidad y baja latencia.
- **Persistencia**: Opciones para garantizar la durabilidad de los mensajes.
- **Simplicidad**: Fácil de configurar y mantener.

## Mejoras Futuras

### Escalabilidad

- **Clusterización**: Implementar múltiples instancias del servidor detrás de un balanceador de carga.
- **Almacenamiento distribuido**: Migrar a un sistema de archivos distribuido para mayor escalabilidad.

### Seguridad

- **Autenticación más robusta**: Implementar OAuth o JWT para la autenticación.
- **Cifrado de archivos**: Cifrar los archivos almacenados en reposo.

### Funcionalidad

- **Interfaz web**: Desarrollar una interfaz web para gestionar archivos.
- **Sincronización de archivos**: Implementar sincronización automática entre cliente y servidor.
- **Versionado de archivos**: Mantener versiones anteriores de los archivos.

### Despliegue

- **Contenedores Docker**: Facilitar el despliegue mediante contenedores.
- **Orquestación con Kubernetes**: Gestionar múltiples instancias del servidor.
