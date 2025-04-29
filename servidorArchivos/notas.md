crear certificados

openssl req -x509 -newkey rsa:4096 -keyout llave.pem -out certificado.pem -days 365 -nodes

# Estructura del Proyecto - Servidor de Archivos

```mermaid
graph TD
    Root[servidorArchivos] --> Servidor[servidor/]
    Root --> BaseDatos[base_datos/]
    Root --> Tareas[tareas/]
    Root --> Cert[certificados/]
    Root --> Test[test/]
    Root --> Doc[documentacion/]
    
    %% Servidor files
    Servidor --> MainPy[main.py]
    Servidor --> ServidorPy[servidor.py]
    Servidor --> ServidorAsyncPy[servidor_async.py]
    Servidor --> ClientePy[cliente.py]
    Servidor --> ComandosPy[comandos.py]
    Servidor --> SeguridadPy[seguridad.py]
    
    %% BaseDatos files
    BaseDatos --> DbPy[db.py]
    BaseDatos --> ConexionPy[conexion.py]
    
    %% Tareas files
    Tareas --> CeleryAppPy[celery_app.py]
    Tareas --> TareasPy[tareas.py]
    
    %% Test files
    Test --> TestServerPy[test_server.py]
    Test --> TestAsyncServerPy[test_async_server.py]
    
    %% Dependencies and relationships
    ServidorPy -.-> DbPy
    ServidorAsyncPy -.-> DbPy
    ServidorPy -.-> SeguridadPy
    ServidorAsyncPy -.-> SeguridadPy
    MainPy -.-> ServidorPy
    MainPy -.-> ServidorAsyncPy
    ServidorPy -.-> ComandosPy
    ServidorAsyncPy -.-> ComandosPy
    ComandosPy -.-> TareasPy
    TareasPy -.-> CeleryAppPy

    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef folder fill:#bbdefb,stroke:#333,stroke-width:1px;
    classDef pythonFile fill:#c8e6c9,stroke:#333,stroke-width:1px;
    
    class Servidor,BaseDatos,Tareas,Cert,Test,Doc folder;
    class MainPy,ServidorPy,ServidorAsyncPy,ClientePy,ComandosPy,SeguridadPy,DbPy,ConexionPy,CeleryAppPy,TareasPy,TestServerPy,TestAsyncServerPy pythonFile;


flowchart TD
    Client[Cliente] <--> Server[Servidor/Servidor Async]
    Server --> CommandHandler[Comandos]
    Server --> Security[Seguridad]
    Server --> Database[Base de Datos]
    CommandHandler --> CeleryTasks[Tareas Celery]
    CeleryTasks --> Redis[Redis]
    
    subgraph Componentes Principales
        Server
        Client
        CommandHandler
        Security
        Database
    end
    
    subgraph Procesamiento Asincrónico
        CeleryTasks
        Redis
    end
    
    classDef component fill:#e3f2fd,stroke:#333,stroke-width:2px;
    classDef external fill:#ffecb3,stroke:#333,stroke-width:2px;
    
    class Server,Client,CommandHandler,Security,Database,CeleryTasks component;
    class Redis external;