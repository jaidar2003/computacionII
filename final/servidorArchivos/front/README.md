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

## Características

- **Autenticación de usuarios**: Inicio de sesión y registro
- **Explorador de archivos**: Visualización de archivos almacenados
- **Gestión de archivos**: Subida, descarga y eliminación de archivos
- **Interfaz responsiva**: Diseñada para funcionar en dispositivos móviles y de escritorio

## Tecnologías Utilizadas

- **TypeScript**: Para tipado estático y mejor desarrollo
- **React**: Biblioteca para construir interfaces de usuario
- **React Router**: Para la navegación entre páginas
- **Styled Components**: Para estilos con CSS-in-JS
- **Axios**: Para realizar peticiones HTTP
- **Vite**: Para el empaquetado y servidor de desarrollo