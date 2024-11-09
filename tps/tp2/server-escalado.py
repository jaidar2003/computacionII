import multiprocessing
import socketserver
from PIL import Image
import io
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO)

class ImageScalingHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logging.info("Received connection")
        # Leer el factor de escala y los datos de la imagen
        scale_factor = int.from_bytes(self.request.recv(4), byteorder='little') / 100  # Leer factor de escala
        data = self.request.recv(1024 * 1024)  # Recibir datos de la imagen
        image = Image.open(io.BytesIO(data))
        logging.info("Image received for scaling")

        # Escalar la imagen
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        scaled_image = image.resize(new_size)
        logging.info("Image scaled")

        # Enviar la imagen escalada de vuelta
        img_byte_arr = io.BytesIO()
        scaled_image.save(img_byte_arr, format='PNG')
        self.request.sendall(img_byte_arr.getvalue())
        logging.info("Scaled image sent back")

def start_scaling_server():
    logging.info("Starting scaling server")
    with socketserver.TCPServer(('127.0.0.1', 8889), ImageScalingHandler) as server:
        server.serve_forever()

def signal_handler(sig, frame):
    logging.info("Shutting down scaling server")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    process = multiprocessing.Process(target=start_scaling_server)
    process.start()
    logging.info("Scaling server process started")
    process.join()