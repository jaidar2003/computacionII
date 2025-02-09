import socket
import ssl

HOST = '127.0.0.1'
PORT = 5000

def iniciar_cliente():
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE

    with socket.create_connection((HOST, PORT)) as sock:
        with contexto.wrap_socket(sock, server_hostname=HOST) as conexion_ssl:
            print(conexion_ssl.recv(1024).decode(), end="")

            while True:
                comando = input("> ")
                if comando.lower() == 'salir':
                    print("Desconectando...")
                    conexion_ssl.sendall(b"SALIR")
                    break

                conexion_ssl.sendall(comando.encode())
                respuesta = conexion_ssl.recv(4096).decode()
                print(respuesta)

if __name__ == "__main__":
    iniciar_cliente()
