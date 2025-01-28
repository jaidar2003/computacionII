Proyecto:
Servidor de Archivos Concurrente con Acceso Remoto

Descripción del Proyecto:
El objetivo de este proyecto es crear un servidor de archivos que permita a múltiples clientes conectarse y acceder a archivos de manera concurrente. El servidor utilizará sockets para la comunicación con los clientes y mecanismos de IPC para gestionar el acceso a los archivos. El servidor también utilizará asincronismo de I/O para mejorar el rendimiento.

Arquitectura del Proyecto

El proyecto consistirá en dos componentes principales:

1. Servidor de Archivos: responsable de gestionar el acceso a los archivos y comunicarse con los clientes.
2. Cliente de Archivos: responsable de conectarse al servidor y acceder a los archivos.

Funcionalidades del Servidor

1. Gestión de Archivos: el servidor será capaz de crear, eliminar, renombrar y listar archivos.
2. Acceso Concurrente: el servidor permitirá a múltiples clientes acceder a los archivos de manera concurrente.
3. Comunicación con Clientes: el servidor utilizará sockets para comunicarse con los clientes.

Funcionalidades del Cliente

1. Conexión al Servidor: el cliente se conectará al servidor utilizando sockets.
2. Acceso a Archivos: el cliente podrá acceder a los archivos del servidor.
3. Gestión de Archivos: el cliente podrá crear, eliminar, renombrar y listar archivos en el servidor.

Mecanismos de IPC

1. Sockets: el servidor y los clientes utilizarán sockets para comunicarse.
2. Asincronismo de I/O: el servidor utilizará asincronismo de I/O para mejorar el rendimiento.

Herramientas de Sincronismo y Conurrencia

1. Threads: el servidor utilizará threads para gestionar el acceso concurrente a los archivos.
2. Locks: el servidor utilizará locks para sincronizar el acceso a los archivos.

Almacenamiento de Datos

1. Sistema de Archivos: el servidor almacenará los archivos en un sistema de archivos local.

Entorno Visual

1. Interfaz de Línea de Comandos: el cliente tendrá una interfaz de línea de comandos para interactuar con el servidor.

Características clave

1. Servidor de archivos: El servidor almacenará archivos en un directorio local.
2. Conexión de clientes: Los clientes se conectarán al servidor utilizando sockets.
3. Acceso concurrente: El servidor permitirá a múltiples clientes acceder a los archivos simultáneamente.
4. Gestión de archivos: El servidor permitirá crear, eliminar, renombrar y listar archivos.

Funcionalidades del servidor

1. Iniciar el servidor y escuchar conexiones de clientes.
2. Autenticar a los clientes y autorizar el acceso a los archivos.
3. Gestionar el acceso concurrente a los archivos.
4. Proporcionar funcionalidades de gestión de archivos (crear, eliminar, renombrar, listar).

Funcionalidades del cliente

1. Conectarse al servidor y autenticarse.
2. Acceder a los archivos del servidor.
3. Realizar operaciones de gestión de archivos (crear, eliminar, renombrar, listar).


