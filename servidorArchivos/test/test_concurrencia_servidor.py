import unittest
import threading
import socket
import ssl
import time
import os
from server.servidor import iniciar_servidor

class TestConcurrenciaServidor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.host = '127.0.0.1'
        cls.port = 5050
        cls.num_clientes = 5
        cls.resultados = []

        # Crear directorio temporal si no existe
        os.makedirs("test_archivos_servidor", exist_ok=True)

        # Lanzar el server en segundo plano
        cls.server_thread = threading.Thread(
            target=iniciar_servidor,
            args=(cls.host, cls.port, "test_archivos_servidor"),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1.5)  # Esperar a que el server inicie

    def cliente_simulado(self, id_cliente):
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((self.host, self.port)) as sock:
                with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    ssock.recv(1024)  # bienvenida
                    ssock.recv(1024)  # pedir usuario
                    ssock.sendall(f"usuario{id_cliente}\n".encode())
                    ssock.recv(1024)  # pedir contraseña
                    ssock.sendall(f"contraseña{id_cliente}\n".encode())
                    respuesta = ssock.recv(1024).decode()
                    self.resultados.append((id_cliente, respuesta.strip()))
        except Exception as e:
            self.resultados.append((id_cliente, f"Error: {e}"))

    def test_conexiones_concurrentes(self):
        hilos = []
        for i in range(self.num_clientes):
            hilo = threading.Thread(target=self.cliente_simulado, args=(i,))
            hilos.append(hilo)
            hilo.start()

        for hilo in hilos:
            hilo.join()

        for id_cliente, respuesta in self.resultados:
            print(f"Cliente {id_cliente}: {respuesta}")
            self.assertIn("✅ Autenticación exitosa", respuesta)


if __name__ == '__main__':
    unittest.main()
