import asyncio
from aiohttp import web
from PIL import Image
import io
import logging

logging.basicConfig(level=logging.INFO)

async def handle(request):
    logging.info("Received request")
    data = await request.post()
    image_data = data['image'].file.read()
    image = Image.open(io.BytesIO(image_data)).convert('L')
    logging.info("Image converted to grayscale")

    # Send the image to the scaling server
    scaled_image = await send_to_scaling_server(image)
    logging.info("Image sent to scaling server and received back")

    # Convert the scaled image to bytes
    img_byte_arr = io.BytesIO()
    scaled_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return web.Response(body=img_byte_arr, content_type='image/png')

async def send_to_scaling_server(image):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8889)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    writer.write(image_bytes.getvalue())
    await writer.drain()
    logging.info("Image sent to scaling server")

    data = await reader.read()
    scaled_image = Image.open(io.BytesIO(data))
    logging.info("Received scaled image from scaling server")

    writer.close()
    await writer.wait_closed()

    return scaled_image

def start_http_server():
    app = web.Application()
    app.add_routes([web.post('/process', handle)])
    web.run_app(app, port=8080)

if __name__ == '__main__':
    start_http_server()