# Usar una imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo del cliente al contenedor
COPY cliente.py ./  # Archivo del cliente

# Instalar dependencias si es necesario
# Por ejemplo, si tienes un requirements.txt:
# COPY requirements.txt ./
# RUN pip install -r requirements.txt

# Comando predeterminado para iniciar el cliente
CMD ["python", "cliente.py"]

