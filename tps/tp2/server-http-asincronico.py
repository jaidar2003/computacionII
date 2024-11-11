import asyncio
from aiohttp import web
from PIL import Image
import io
import logging
import socket

logging.basicConfig(level=logging.INFO)

async def handle(request):
    logging.info("Received request")
    data = await request.post()
    image_data = data['image'].file.read()
    image = Image.open(io.BytesIO(image_data)).convert('L')
    logging.info("Image converted to grayscale")

    # Send the image to the scaling server with a scale factor
    scale_factor = 50  # Example scale factor (50%)
    scaled_image = await send_to_scaling_server(image, scale_factor)
    logging.info("Image sent to scaling server and received back")

    # Convert the scaled image to bytes
    img_byte_arr = io.BytesIO()
    scaled_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return web.Response(body=img_byte_arr, content_type='image/png')

async def send_to_scaling_server(image, scale_factor):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8889)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')

    # Send the scale factor first
    writer.write(scale_factor.to_bytes(4, byteorder='little'))
    await writer.drain()

    # Send the image data
    writer.write(image_bytes.getvalue())
    await writer.drain()
    logging.info("Image sent to scaling server")

    data = await reader.read()
    scaled_image = Image.open(io.BytesIO(data))
    logging.info("Received scaled image from scaling server")

    writer.close()
    await writer.wait_closed()

    return scaled_image

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_http_server():
    app = web.Application(client_max_size=2*1024*1024)  # Increase max size to 2MB
    app.add_routes([web.post('/process', handle)])
    port = 8080
    while is_port_in_use(port):
        port += 1
    web.run_app(app, port=port)

if __name__ == '__main__':
    start_http_server()