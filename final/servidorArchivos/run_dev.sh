#!/bin/bash

# Colores para mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando entorno de desarrollo para Servidor de Archivos ===${NC}"

# Verificar si estamos en un entorno virtual
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${RED}No se detectó un entorno virtual activo.${NC}"
    echo -e "Se recomienda activar un entorno virtual antes de ejecutar este script."
    read -p "¿Desea continuar de todos modos? (s/n): " CONTINUE
    if [[ "$CONTINUE" != "s" && "$CONTINUE" != "S" ]]; then
        echo "Saliendo..."
        exit 1
    fi
fi

# Instalar dependencias de Python si no están instaladas
echo -e "${BLUE}Verificando dependencias de Python...${NC}"
pip install -q flask flask-cors

# Verificar si npm está instalado
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm no está instalado. Por favor, instale Node.js y npm.${NC}"
    exit 1
fi

# Instalar dependencias de Node.js si no están instaladas
echo -e "${BLUE}Instalando dependencias de Node.js...${NC}"
cd front
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias de Node.js (esto puede tardar unos minutos)..."
    npm install
else
    echo "Las dependencias de Node.js ya están instaladas."
fi

# Iniciar el servidor de archivos en segundo plano
echo -e "${BLUE}Iniciando servidor de archivos...${NC}"
cd ..
python -m server.servidor &
SERVER_PID=$!

# Iniciar el servidor Flask en segundo plano
echo -e "${BLUE}Iniciando servidor Flask API...${NC}"
python -m api.app &
FLASK_PID=$!

# Iniciar el servidor de desarrollo de Vite
echo -e "${BLUE}Iniciando servidor de desarrollo de Vite...${NC}"
cd front
npm run dev &
VITE_PID=$!

# Función para manejar la terminación del script
cleanup() {
    echo -e "${BLUE}Deteniendo servidores...${NC}"
    kill $SERVER_PID
    kill $FLASK_PID
    kill $VITE_PID
    exit 0
}

# Capturar señales de terminación
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}¡Entorno de desarrollo iniciado!${NC}"
echo -e "API Flask: http://localhost:5000"
echo -e "Frontend: http://localhost:5173"
echo -e "Presiona Ctrl+C para detener ambos servidores."

# Mantener el script en ejecución
wait
