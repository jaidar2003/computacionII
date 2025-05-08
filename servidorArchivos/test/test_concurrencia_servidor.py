
import unittest
import socket
import ssl
import threading
import time
import sys
import os

# Agregar el path raíz para importar correctamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.servidor import iniciar_servidor

HOST = '127.0.0.1'
PORT = 5055  # Usar puerto diferente para pruebas

class TestConcurrenciaServidorExtendido(unittest.TestCase):
    def setUp(self):
        self.directorio_base = "archivos_servidor_test"
        self.servidor_thread = threading.Thread(
            target=iniciar_servidor, args=(HOST, PORT, self.directorio_base), daemon=True)
        self.servidor_thread.start()
        time.sleep(1)  # Esperar a que el servidor se inicie

    def test_multiples_conexiones_simultaneas(self):
        clientes = []
        resultados = []

        def cliente_job():
            try:
                context = ssl._create_unverified_context()
                with socket.create_connection((HOST, PORT)) as sock:
                    with context.wrap_socket(sock, server_hostname=HOST) as s:
                        s.recv(1024)
                        s.sendall(b"testuser\n")
                        s.recv(1024)
                        s.sendall(b"password123\n")
                        s.recv(1024)
                        s.sendall(b"SALIR\n")
            except Exception as e:
                print(f"[ERROR] Cliente falló: {e}")
                resultados.append(False)
            else:
                resultados.append(True)

        for _ in range(5):
            t = threading.Thread(target=cliente_job)
            clientes.append(t)
            t.start()

        for t in clientes:
            t.join()

        self.assertTrue(all(resultados), "No todas las conexiones se completaron exitosamente.")

if __name__ == '__main__':
    unittest.main()
