import requests

# Ruta a la imagen que quieres enviar
image_path = 'imagen.png'

# URL del servidor HTTP
url = 'http://127.0.0.1:8080/process'

# Enviar la imagen al servidor HTTP
with open(image_path, 'rb') as image_file:
    files = {'image': image_file}
    response = requests.post(url, files=files)

# Guardar la imagen procesada devuelta por el servidor
if response.status_code == 200:
    with open('resultado.png', 'wb') as output_file:
        output_file.write(response.content)
    print("Imagen procesada guardada como 'resultado.png'")
else:
    print("Error en el procesamiento:", response.text)
