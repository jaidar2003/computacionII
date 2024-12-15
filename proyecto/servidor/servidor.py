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
        self.archivos = {}

    def manejar_conexion(self, cliente_socket):
        while True:
            mensaje = cliente_socket.recv(1024).decode()
            if mensaje == 'listar':
                self.listar_archivos(cliente_socket)
            elif mensaje.startswith('descargar '):
                self.descargar_archivo(cliente_socket, mensaje[10:])
            elif mensaje.startswith('subir '):
                self.subir_archivo(cliente_socket, mensaje[6:])
            elif mensaje == 'salir':
                break
            else:
                cliente_socket.sendall('Comando no reconocido'.encode())

    def listar_archivos(self, cliente_socket):
        archivos = os.listdir('archivos')
        lista_archivos = '\n'.join(archivos)
        cliente_socket.sendall(lista_archivos.encode())

    def descargar_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join('archivos', nombre_archivo)
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'rb') as archivo:
                datos = archivo.read()
                cliente_socket.sendall(datos)
        else:
            cliente_socket.sendall('Archivo no encontrado'.encode())

    def subir_archivo(self, cliente_socket, nombre_archivo):
        ruta_archivo = os.path.join('archivos', nombre_archivo)
        with open(ruta_archivo, 'wb') as archivo:
            while True:
                datos = cliente_socket.recv(1024)
                if not datos:
                    break
                archivo.write(datos)
        cliente_socket.sendall('Archivo subido correctamente'.encode())

    def iniciar(self):
        print(f'Servidor iniciado en {self.host}:{self.puerto}')
        while True:
            cliente_socket, direccion = self.socket_servidor.accept()
            print(f'Conexión establecida con {direccion}')
            hilo = threading.Thread(target=self.manejar_conexion, args=(cliente_socket,))
            hilo.start()


if __name__ == '__main__':
    servidor = ServidorArchivos()
    servidor.iniciar()