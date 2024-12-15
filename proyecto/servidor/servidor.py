import socket
import threading
import os

class ServidorArchivos:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(5)
        self.directorio_archivos = 'archivos'  # Directorio donde se almacenan los archivos

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
        lista_archivos = '\n'.join(archivos) if archivos else 'No hay archivos disponibles'
        cliente_socket.sendall(lista_archivos.encode())

    def descargar_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join(self.directorio_archivos, nombre_archivo)
        if os.path.isfile(ruta_archivo):
            cliente_socket.sendall('OK'.encode())  # Confirmación inicial
            with open(ruta_archivo, 'rb') as archivo:
                while chunk := archivo.read(1024):
                    cliente_socket.sendall(chunk)
            cliente_socket.sendall(b'FIN')  # Señal de terminación
        else:
            cliente_socket.sendall('Archivo no encontrado'.encode())

    def subir_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join(self.directorio_archivos, nombre_archivo)
        cliente_socket.sendall('OK'.encode())  # Confirmación inicial
        with open(ruta_archivo, 'wb') as archivo:
            while True:
                datos = cliente_socket.recv(1024)
                if datos.endswith(b'FIN'):  # Señal para finalizar recepción
                    archivo.write(datos[:-3])
                    break
                archivo.write(datos)
        cliente_socket.sendall('Archivo subido correctamente'.encode())

    def iniciar(self):
        print(f'Servidor iniciado en {self.host}:{self.puerto}')
        if not os.path.exists(self.directorio_archivos):
            os.makedirs(self.directorio_archivos)
        try:
            while True:
                cliente_socket, direccion = self.socket_servidor.accept()
                hilo = threading.Thread(target=self.manejar_conexion, args=(cliente_socket, direccion))
                hilo.start()
        except KeyboardInterrupt:
            print('Servidor detenido manualmente.')
        finally:
            self.socket_servidor.close()


if __name__ == '__main__':
    servidor = ServidorArchivos()
    servidor.iniciar()
