# Guía de ejecución (RUN.md)

## Introducción
Esta guía resume cómo poner en marcha todos los componentes del proyecto y cómo utilizar el CLI integrado. Está optimizada para ejecución local en macOS y Linux, e incluye notas y resolución de problemas habituales.

---

## Componentes necesarios
Para que el sistema funcione correctamente, ejecuta TRES componentes:

1) Servidor principal (gestiona archivos y conexiones via sockets SSL)
2) API Flask (interfaz que consume el frontend)
3) Worker de Celery (procesa verificaciones en segundo plano)

Importante: Si el worker de Celery no está corriendo, las verificaciones de archivos no funcionarán correctamente.

---

## Puertos y direcciones clave
- API Flask: escucha en 0.0.0.0:5007 (fijo en el código)
- Servidor de archivos: por defecto SERVER_PORT=5005 (se puede ajustar con -p o en .env)
- Frontend (Vite): por defecto http://localhost:5173 con proxy a la API en http://localhost:5007

Notas:
- El comando `main.py -m api -H ... -p ...` NO cambia el puerto de Flask (sigue en 5007). Esos parámetros son para que la API se conecte al servidor de archivos en el host/puerto que indiques.
- Ajusta `VITE_API_URL` en `front/.env` si la API está en otra IP o puerto.

---

## macOS

### 1) Iniciar el servidor de archivos (terminal A)
```bash
python /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/main.py -m server
# Opcional: especificar IP/puerto si es necesario
# python .../main.py -m server -H 127.0.0.1 -p 5005
```

### 2) Iniciar la API Flask (terminal B)
```bash
python /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/main.py -m api -H 192.168.100.191 -p 5005
# Recuerda: Flask escucha fijo en 5007; -H/-p es para la conexión desde la API al servidor de archivos.
```

### 3) Iniciar el worker de Celery (terminal C) — Recomendado/Obligatorio para verificaciones
```bash
cd /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos
celery -A tareas.celery worker --loglevel=info
```

### 4) Iniciar el frontend (terminal D)
```bash
cd /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/front
# Verifica o edita front/.env si la API está en otra máquina:
# VITE_API_URL=http://localhost:5007
npm run dev
```

---

## Linux

### 1) Iniciar el servidor de archivos (terminal A)
```bash
python /home/juanma/PycharmProjects/computacionII/final/servidorArchivos/main.py -m server
```

### 2) Iniciar la API Flask (terminal B)
```bash
python /home/juanma/PycharmProjects/computacionII/final/servidorArchivos/main.py -m api -H 192.168.100.191 -p 5005
```

### 3) Iniciar el worker de Celery (terminal C)
```bash
cd /home/juanma/PycharmProjects/computacionII/final/servidorArchivos
celery -A tareas.celery worker --loglevel=info
```

### 4) Iniciar el frontend (terminal D)
```bash
cd /home/juanma/PycharmProjects/computacionII/final/servidorArchivos/front
# Ajusta VITE_API_URL si la API está en otra IP/puerto
npm run dev
```

---

## Usando el CLI integrado (Nueva funcionalidad)

El CLI se comunica directamente con el servidor mediante sockets SSL (no usa la API Flask). Asegúrate de tener el servidor corriendo antes de usarlo.

### Paso 1: Instalar dependencias del CLI
```bash
pip install colorama tqdm
```

### Paso 2: Forma recomendada — Usar main.py directamente
Desde la carpeta servidorArchivos:
```bash
cd /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos
python main.py -m cli
```
Esto lanza automáticamente el menú numerado.

### Paso 3: Opciones del CLI
Actualmente solo está soportado el menú interactivo:
```bash
python main.py -m cli
```

### Paso 4: Nota
Se eliminaron métodos alternativos y wrappers. Usa únicamente:
```bash
python main.py -m cli
```

### Paso 5: Configuración del CLI
- Detecta automáticamente SERVER_HOST/SERVER_PORT desde el archivo .env
- Para cambiar host/puerto en la ejecución:
```bash
python main.py -m cli -H 192.168.100.191 -p 1608
```

---

## Menús disponibles en el CLI

### Menú principal (sin sesión iniciada)
1. Iniciar sesión  
2. Registrarse  
3. Salir

### Menú principal (con sesión iniciada)
4. Listar archivos  
5. Subir archivo  
6. Descargar archivo  
7. Eliminar archivo  
8. Renombrar archivo  
9. Verificar archivo  
10. Cerrar sesión

### Opciones adicionales (administradores)
11. Listar usuarios  
12. Ver solicitudes de permisos  
13. Aprobar/rechazar solicitud

### Opciones adicionales (usuarios)
11. Solicitar permisos de administrador  
12. Ver mis solicitudes de permisos

---

## Cambios importantes en esta actualización

- CLI integrado: se ejecuta directamente desde main.py con -m cli  
- Menú por defecto: `python main.py -m cli` lanza el menú numerado  
- Configuración automática: detecta SERVER_HOST/SERVER_PORT del .env  
- Sin advertencias por variables faltantes  
- CLI simplificado: solo menú interactivo disponible  
- Estructura: CLI movido a servidorArchivos/cli/  
- API Flask fija en 0.0.0.0:5007; -H/-p en -m api apuntan al servidor de archivos

---

## Recomendación de uso (rápido)

```bash
cd /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos
python main.py -m cli
```

Eso es todo: aparecerá el menú numerado y podrás navegar de forma intuitiva.

---

## Variables de entorno (resumen útil)

- SERVER_HOST y SERVER_PORT: host/puerto del servidor de archivos  
- SERVIDOR_DIR: carpeta donde se almacenan archivos  
- VITE_API_URL (frontend/front/.env): URL de la API Flask (ej: http://localhost:5007)  
- CELERY_PATH (opcional): ruta al ejecutable de celery si no está en el PATH

Edición rápida del .env:
```bash
nano /Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/.env
```

---

## Verificación rápida

- Frontend: http://localhost:5173  
- API: http://localhost:5007/api/check-auth debería responder JSON  
- Si usas Vite, no deberían aparecer “http proxy error: /api/... ECONNREFUSED” si la API está arriba

---

## Resolución de problemas

- ECONNREFUSED en Vite:
  - Asegúrate de que la API Flask esté corriendo en 5007
  - Verifica VITE_API_URL en front/.env
  - Reinicia `npm run dev` si cambiaste `.env`

- Login falla:
  - Revisa que el servidor de archivos esté activo y que la API lo apunte con -H/-p correctos
  - Celery no es necesario para login, pero sí para verificaciones

- Puerto 5007 en uso:
  - Detén procesos anteriores de Flask o libera el puerto

- IP incorrecta al iniciar server:
  - El sistema te sugerirá la IP local detectada y cómo pasarla por línea de comandos (-H)

---

## Documentación adicional

Para más información, consulta:
- `/Users/juanmaaidar/PycharmProjects/computacionII/final/servidorArchivos/INSTRUCCIONES_MENU_CLI_ACTUALIZADO.md`

---

> Nota: Este archivo es la versión Markdown de `run.txt`. El archivo de texto sigue existiendo para referencias legacy, pero se recomienda usar este RUN.md como fuente principal de instrucciones.
