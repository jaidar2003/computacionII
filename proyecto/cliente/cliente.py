import socket
import os

class ClienteArchivos:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_cliente.connect((self.host, self.puerto))

    def listar_archivos(self):
        self.socket_cliente.sendall('listar'.encode())
        respuesta = self.socket_cliente.recv(4096).decode()
        print('Archivos disponibles:\n' + respuesta)

    def descargar_archivo(self, nombre_archivo):
        self.socket_cliente.sendall(f'descargar {nombre_archivo}'.encode())
        confirmacion = self.socket_cliente.recv(1024).decode()
        if confirmacion == 'OK':
            with open(nombre_archivo, 'wb') as archivo:
                while True:
                    datos = self.socket_cliente.recv(1024)
                    if datos.endswith(b'FIN'):
                        archivo.write(datos[:-3])
                        break
                    archivo.write(datos)
            print('Archivo descargado correctamente.')
        else:
            print(confirmacion)

    def subir_archivo(self, nombre_archivo):
        if not os.path.isfile(nombre_archivo):
            print('El archivo no existe.')
            return
        self.socket_cliente.sendall(f'subir {nombre_archivo}'.encode())
        confirmacion = self.socket_cliente.recv(1024).decode()
        if confirmacion == 'OK':
            with open(nombre_archivo, 'rb') as archivo:
                while chunk := archivo.read(1024):
                    self.socket_cliente.sendall(chunk)
            self.socket_cliente.sendall(b'FIN')
            respuesta = self.socket_cliente.recv(1024).decode()
            print(respuesta)

    def salir(self):
        self.socket_cliente.sendall('salir'.encode())
        self.socket_cliente.close()
        print('Desconectado del servidor.')


def menu_principal():
    cliente = ClienteArchivos()
    while True:
        print('\nOpciones:')
        print('1. Listar archivos')
        print('2. Descargar archivo')
        print('3. Subir archivo')
        print('4. Salir')
        opcion = input('Ingrese una opción: ')
        if opcion == '1':
            cliente.listar_archivos()
        elif opcion == '2':
            nombre_archivo = input('Ingrese el nombre del archivo a descargar: ')
            cliente.descargar_archivo(nombre_archivo)
        elif opcion == '3':
            nombre_archivo = input('Ingrese el nombre del archivo a subir: ')
            cliente.subir_archivo(nombre_archivo)
        elif opcion == '4':
            cliente.salir()
            break
        else:
            print('Opción inválida.')

if __name__ == '__main__':
    menu_principal()
    cliente = ClienteArchivos()