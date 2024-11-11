import multiprocessing
import socketserver
from PIL import Image
import io
import logging
import signal
import sys
import socket

logging.basicConfig(level=logging.INFO)

class ImageScalingHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logging.info("Received connection")
        scale_factor = int.from_bytes(self.request.recv(4), byteorder='little') / 100
        data = self.request.recv(1024 * 1024)
        logging.info(f"Received data of length: {len(data)}")

        try:
            image = Image.open(io.BytesIO(data))
            logging.info("Image received for scaling")

            new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
            scaled_image = image.resize(new_size)
            logging.info("Image scaled")

            img_byte_arr = io.BytesIO()
            scaled_image.save(img_byte_arr, format='PNG')
            self.request.sendall(img_byte_arr.getvalue())
            logging.info("Scaled image sent back")
        except Exception as e:
            logging.error(f"Failed to process image: {e}")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_scaling_server():
    port = 8889
    while is_port_in_use(port):
        port += 1
    with socketserver.TCPServer(('127.0.0.1', port), ImageScalingHandler) as server:
        logging.info(f"Scaling server started on port {port}")
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