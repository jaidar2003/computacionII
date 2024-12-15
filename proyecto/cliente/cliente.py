import socket

class ClienteArchivos:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_cliente.connect((self.host, self.puerto))

    def listar_archivos(self):
        self.socket_cliente.sendall('listar'.encode())
        respuesta = self.socket_cliente.recv(1024).decode()
        print(respuesta)

    def descargar_archivo(self, nombre_archivo):
        self.socket_cliente.sendall(f'descargar {nombre_archivo}'.encode())
        with open(nombre_archivo, 'wb') as archivo:
            while True:
                datos = self.socket_cliente.recv(1024)
                if not datos:
                    break
                archivo.write(datos)
        print('Archivo descargado correctamente')

    def subir_archivo(self, nombre_archivo):
        self.socket_cliente.sendall(f'subir {nombre_archivo}'.encode())
        with open(nombre_archivo, 'rb') as archivo:
            datos = archivo.read()
            self.socket_cliente.sendall(datos)
        respuesta = self.socket_cliente.recv(1024).decode()
        print(respuesta)

    def salir(self):
        self.socket_cliente.sendall('salir'.encode())
        self.socket_cliente.close()

if __name__ == '__main__':
    cliente = ClienteArchivos()
    while True:
        print('Opciones:')
        print('1. Listar archivos')
        print('2. Descargar archivo')
        print('3. Subir archivo')
        print('4. Salir')
        opcion = input('Ingrese una opción: ')
        if opcion == '1':
            cliente.listar_archivos()
        elif opcion == '2':
            nombre_archivo = input('Ingrese el nombre del archivo: ')
            cliente.descargar_archivo(nombre_archivo)
