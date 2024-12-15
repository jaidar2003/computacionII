# Usar una imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos necesarios al contenedor
COPY servidor.py ./  # Archivo del servidor
COPY archivos ./archivos  # Carpeta para almacenar los archivos

# Instalar dependencias si es necesario
# Por ejemplo, si tienes un requirements.txt:
# COPY requirements.txt ./
# RUN pip install -r requirements.txt

# Exponer el puerto en el que el servidor escucha
EXPOSE 8080

# Comando para ejecutar el servidor
CMD ["python", "servidor.py"]
