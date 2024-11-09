import multiprocessing
import subprocess
import argparse
from PIL import Image
import os
import socket
import requests

def main():
    parser = argparse.ArgumentParser(description='Process an image.')
    parser.add_argument('--input', default='/home/juanma/PycharmProjects/compu2/tps/tp2/entrada.png', help='Path to the input image')
    args = parser.parse_args()

    input_path = args.input

    if not os.path.exists(input_path):
        print(f"Error: The file {input_path} does not exist.")
        return

    try:
        image = Image.open(input_path)
        print(f"Successfully loaded image: {input_path}")
        send_image_for_processing(input_path)
    except Exception as e:
        print(f"Error loading image: {e}")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_scaling_server():
    port = 8889
    if is_port_in_use(port):
        print(f"Port {port} is in use, trying another port.")
        port = 8890  # Use a different port if 8889 is in use
    subprocess.run(['python3', '/home/juanma/PycharmProjects/compu2/tps/tp2/server-escalado.py', str(port)])

def start_http_server():
    subprocess.run(['python3', '/home/juanma/PycharmProjects/compu2/tps/tp2/server-http-asincronico.py'])

def send_image_for_processing(image_path):
    url = 'http://127.0.0.1:8080/process'
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        with open('resultado.png', 'wb') as output_file:
            output_file.write(response.content)
        print("Imagen procesada guardada como 'resultado.png'")
    else:
        print("Error en el procesamiento:", response.text)

if __name__ == '__main__':
    scaling_process = multiprocessing.Process(target=start_scaling_server)
    http_process = multiprocessing.Process(target=start_http_server)

    scaling_process.start()
    http_process.start()

    scaling_process.join()
    http_process.join()

    main()