import multiprocessing
import socketserver
from PIL import Image
import io


class ImageScalingHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024 * 1024)
        image = Image.open(io.BytesIO(data))

        # Escalar la imagen
        scale_factor = 0.5  # Ejemplo de factor de escala
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        scaled_image = image.resize(new_size)

        img_byte_arr = io.BytesIO()
        scaled_image.save(img_byte_arr, format='PNG')
        self.request.sendall(img_byte_arr.getvalue())


def start_scaling_server():
    with socketserver.TCPServer(('127.0.0.1', 8888), ImageScalingHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    process = multiprocessing.Process(target=start_scaling_server)
    process.start()
    process.join()