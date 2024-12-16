import socket
import ssl

# Configuración del cliente
HOST = '127.0.0.1'
PORT = 5000

def iniciar_cliente():
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE  # Desactiva verificación (solo para desarrollo)

    with socket.create_connection((HOST, PORT)) as sock:
        with contexto.wrap_socket(sock, server_hostname=HOST) as conexion_ssl:
            print(conexion_ssl.recv(1024).decode(), end="")  # Mensaje de bienvenida

            while True:
                comando = input()
                conexion_ssl.sendall(comando.encode())
                respuesta = conexion_ssl.recv(4096).decode()
                print(respuesta, end="")
                if "Desconectando" in respuesta:
                    break

if __name__ == "__main__":
    iniciar_cliente()