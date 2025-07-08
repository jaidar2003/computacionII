# Servidor de Archivos - Frontend

Este es el frontend para el Servidor de Archivos Seguro, implementado con TypeScript y React.

## Requisitos

- Node.js (v14 o superior)
- npm (v6 o superior)
- El servidor backend debe estar en ejecución

## Estructura del Proyecto

```
front/
├── public/           # Archivos estáticos
├── src/              # Código fuente
│   ├── components/   # Componentes reutilizables
│   ├── contexts/     # Contextos de React (AuthContext)
│   └── pages/        # Componentes de página
├── index.html        # Punto de entrada HTML
├── package.json      # Dependencias y scripts
├── tsconfig.json     # Configuración de TypeScript
└── vite.config.ts    # Configuración de Vite
```

## Instalación

1. Asegúrate de tener Node.js y npm instalados:
   ```bash
   node --version
   npm --version
   ```

2. Instala las dependencias:
   ```bash
   cd final/servidorArchivos/front
   npm install
   ```

## Desarrollo

Para iniciar el servidor de desarrollo:

```bash
npm run dev
```

Esto iniciará el servidor de desarrollo de Vite en http://localhost:5173.

## Construcción para Producción

Para construir la aplicación para producción:

```bash
npm run build
```

Esto generará los archivos optimizados en el directorio `dist/`.

## Ejecución Completa (Frontend + Backend)

Para ejecutar tanto el frontend como el backend juntos, puedes usar el script de desarrollo:

```bash
cd final/servidorArchivos
chmod +x run_dev.sh
./run_dev.sh
```

Este script:
1. Verifica las dependencias necesarias
2. Instala las dependencias de Python y Node.js si es necesario
3. Inicia el servidor Flask API
4. Inicia el servidor de desarrollo de Vite
5. Proporciona URLs para acceder a ambos servicios

## Componentes Principales

### Páginas

El frontend está organizado en varias páginas principales:

- **Login (`/src/pages/Login.tsx`)**: Página de inicio de sesión con formulario de autenticación.
- **Register (`/src/pages/Register.tsx`)**: Página de registro para nuevos usuarios.
- **Dashboard (`/src/pages/Dashboard.tsx`)**: Página principal que muestra los archivos del usuario y permite gestionarlos.
- **NotFound (`/src/pages/NotFound.tsx`)**: Página de error 404 para rutas no encontradas.

### Contextos

- **AuthContext (`/src/contexts/AuthContext.tsx`)**: Gestiona el estado de autenticación del usuario en toda la aplicación.
  - Proporciona funciones para iniciar sesión, registrarse y cerrar sesión.
  - Almacena información del usuario autenticado.
  - Verifica el estado de autenticación al cargar la aplicación.

### Componentes Reutilizables

El frontend utiliza varios componentes reutilizables:

- **Button**: Botón estilizado con diferentes variantes.
- **Input**: Campo de entrada estilizado con validación.
- **FileList**: Lista de archivos con opciones de selección.
- **FileItem**: Elemento individual de la lista de archivos.
- **ProgressBar**: Barra de progreso para la subida de archivos.

## Flujo de Trabajo

1. **Autenticación**:
   - El usuario accede a la aplicación y es redirigido a la página de inicio de sesión si no está autenticado.
   - Puede iniciar sesión con credenciales existentes o registrarse como nuevo usuario.
   - Una vez autenticado, se almacena la sesión y se redirige al Dashboard.

2. **Gestión de Archivos**:
   - En el Dashboard, el usuario puede ver la lista de sus archivos.
   - Puede subir nuevos archivos mediante el botón "Subir Archivo".
   - Puede seleccionar un archivo para ver opciones adicionales (descargar, eliminar).
   - La subida de archivos muestra una barra de progreso en tiempo real.

3. **Cierre de Sesión**:
   - El usuario puede cerrar sesión en cualquier momento desde el Dashboard.
   - Esto elimina la sesión y redirige a la página de inicio de sesión.

## Comunicación con el Backend

El frontend se comunica con el backend a través de una API REST:

- **Autenticación**:
  - `GET /api/check-auth`: Verifica si el usuario está autenticado.
  - `POST /api/login`: Inicia sesión con nombre de usuario y contraseña.
  - `POST /api/register`: Registra un nuevo usuario.
  - `POST /api/logout`: Cierra la sesión del usuario.

- **Operaciones de Archivos**:
  - `GET /api/files`: Obtiene la lista de archivos del usuario.
  - `POST /api/files/upload`: Sube un archivo al servidor.
  - `GET /api/files/download/<filename>`: Descarga un archivo del servidor.
  - `DELETE /api/files/<filename>`: Elimina un archivo del servidor.

## Características

- **Autenticación de usuarios**: Inicio de sesión y registro
- **Explorador de archivos**: Visualización de archivos almacenados
- **Gestión de archivos**: Subida, descarga y eliminación de archivos
- **Interfaz responsiva**: Diseñada para funcionar en dispositivos móviles y de escritorio
- **Feedback visual**: Barras de progreso, mensajes de error y éxito
- **Protección de rutas**: Redirección automática a login si no hay sesión

## Tecnologías Utilizadas

- **TypeScript**: Para tipado estático y mejor desarrollo
- **React**: Biblioteca para construir interfaces de usuario
- **React Router**: Para la navegación entre páginas
- **Styled Components**: Para estilos con CSS-in-JS
- **Axios**: Para realizar peticiones HTTP
- **Vite**: Para el empaquetado y servidor de desarrollo
- **React Icons**: Para iconos de interfaz
- **React Context API**: Para gestión de estado global

## Mejores Prácticas Implementadas

- **Componentes Funcionales**: Uso de React Hooks en lugar de componentes de clase.
- **Tipado Estricto**: TypeScript para prevenir errores en tiempo de compilación.
- **Separación de Responsabilidades**: Componentes, contextos y páginas bien definidos.
- **Manejo de Errores**: Captura y visualización de errores de API.
- **Diseño Responsivo**: Interfaz adaptable a diferentes tamaños de pantalla.
- **Código Limpio**: Nombres descriptivos, comentarios y estructura organizada.

## Documentación Adicional

Para obtener información más detallada sobre el proyecto completo, consulta los siguientes archivos en el directorio de documentación:

- **README.md**: Documentación general del proyecto
- **INFO.md**: Informe técnico con decisiones de diseño y justificaciones
- **INSTALL.md**: Instrucciones detalladas de instalación
- **SSL.md**: Configuración de SSL para comunicación segura
- **TODO.md**: Lista de mejoras planificadas para el futuro
