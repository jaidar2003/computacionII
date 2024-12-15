import os
import socket
import threading
import asyncio

class ServidorArchivos:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.directorio_archivos = './archivos'
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(5)
        print(f'Servidor escuchando en {self.host}:{self.puerto}')

    def manejar_conexion(self, cliente_socket, direccion):
        print(f'Conexión establecida con {direccion}')
        try:
            while True:
                mensaje = cliente_socket.recv(1024).decode()
                if not mensaje:
                    break
                if mensaje == 'listar':
                    self.listar_archivos(cliente_socket)
                elif mensaje.startswith('descargar '):
                    nombre_archivo = mensaje.split(' ', 1)[1]
                    self.descargar_archivo(cliente_socket, nombre_archivo)
                elif mensaje.startswith('subir '):
                    nombre_archivo = mensaje.split(' ', 1)[1]
                    self.subir_archivo(cliente_socket, nombre_archivo)
                elif mensaje.startswith('crear '):
                    nombre_archivo = mensaje.split(' ', 1)[1]
                    self.crear_archivo(cliente_socket, nombre_archivo)
                elif mensaje.startswith('eliminar '):
                    nombre_archivo = mensaje.split(' ', 1)[1]
                    self.eliminar_archivo(cliente_socket, nombre_archivo)
                elif mensaje.startswith('renombrar '):
                    nombres = mensaje.split(' ', 2)[1:]
                    self.renombrar_archivo(cliente_socket, nombres[0], nombres[1])
                elif mensaje == 'salir':
                    print(f'Cliente {direccion} desconectado.')
                    break
                else:
                    cliente_socket.sendall('Comando no reconocido'.encode())
        except Exception as e:
            print(f'Error con {direccion}: {e}')
        finally:
            cliente_socket.close()

    def listar_archivos(self, cliente_socket):
        archivos = os.listdir(self.directorio_archivos)
        cliente_socket.sendall('\n'.join(archivos).encode())

    def descargar_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join(self.directorio_archivos, nombre_archivo)
        if os.path.exists(ruta_archivo):
            cliente_socket.sendall('OK'.encode())
            with open(ruta_archivo, 'rb') as archivo:
                while chunk := archivo.read(1024):
                    cliente_socket.sendall(chunk)
            cliente_socket.sendall(b'FIN')
        else:
            cliente_socket.sendall('Archivo no encontrado'.encode())

    def subir_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join(self.directorio_archivos, nombre_archivo)
        cliente_socket.sendall('OK'.encode())
        with open(ruta_archivo, 'wb') as archivo:
            while True:
                datos = cliente_socket.recv(1024)
                if datos.endswith(b'FIN'):
                    archivo.write(datos[:-3])
                    break
                archivo.write(datos)
        cliente_socket.sendall('Archivo subido correctamente'.encode())

    def crear_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join(self.directorio_archivos, nombre_archivo)
        if not os.path.exists(ruta_archivo):
            open(ruta_archivo, 'w').close()
            cliente_socket.sendall('Archivo creado'.encode())
        else:
            cliente_socket.sendall('El archivo ya existe'.encode())

    def eliminar_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join(self.directorio_archivos, nombre_archivo)
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            cliente_socket.sendall('Archivo eliminado'.encode())
        else:
            cliente_socket.sendall('Archivo no encontrado'.encode())

    def renombrar_archivo(self, cliente_socket, nombre_actual, nombre_nuevo):
        ruta_actual = os.path.join(self.directorio_archivos, nombre_actual)
        ruta_nueva = os.path.join(self.directorio_archivos, nombre_nuevo)
        if os.path.exists(ruta_actual):
            os.rename(ruta_actual, ruta_nueva)
            cliente_socket.sendall('Archivo renombrado'.encode())
        else:
            cliente_socket.sendall('Archivo no encontrado'.encode())

    def iniciar(self):
        while True:
            cliente_socket, direccion = self.socket_servidor.accept()
            threading.Thread(target=self.manejar_conexion, args=(cliente_socket, direccion)).start()

class ServidorArchivosAsync:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.directorio_archivos = './archivos'

    async def manejar_conexion(self, reader, writer):
        direccion = writer.get_extra_info('peername')
        print(f'Conexión establecida con {direccion}')
        try:
            while True:
                data = await reader.read(1024)
                mensaje = data.decode()
                if not mensaje:
                    break
                # Manejar comandos como en el ejemplo anterior
        except Exception as e:
            print(f'Error con {direccion}: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def iniciar(self):
        server = await asyncio.start_server(self.manejar_conexion, self.host, self.puerto)
        async with server:
            await server.serve_forever()

if __name__ == '__main__':
    servidor = ServidorArchivos()
    servidor.iniciar()