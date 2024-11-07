import asyncio
from aiohttp import web
from PIL import Image
import io


async def handle(request):
    data = await request.post()
    image_data = data['image'].file.read()
    image = Image.open(io.BytesIO(image_data)).convert('L')

    # Enviar la imagen al servidor de escalado
    scaled_image = await send_to_scaling_server(image)

    # Convertir la imagen escalada a bytes
    img_byte_arr = io.BytesIO()
    scaled_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return web.Response(body=img_byte_arr, content_type='image/png')


async def send_to_scaling_server(image):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    writer.write(image_bytes.getvalue())
    await writer.drain()

    data = await reader.read()
    scaled_image = Image.open(io.BytesIO(data))

    writer.close()
    await writer.wait_closed()

    return scaled_image


app = web.Application()
app.add_routes([web.post('/process', handle)])

if __name__ == '__main__':
    web.run_app(app, port=8080)