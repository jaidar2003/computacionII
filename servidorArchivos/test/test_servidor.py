import unittest
import os
import sys
import tempfile
import socket
import ssl
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.servidor import manejar_cliente, iniciar_servidor

class TestServidor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directorio_base = self.temp_dir.name
        self.mock_conexion = MagicMock()
        self.mock_direccion = ('127.0.0.1', 12345)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('server.seguridad.autenticar_usuario_en_servidor')
    @patch('server.comandos.manejar_comando')
    def test_manejar_cliente_autenticacion_exitosa(self, mock_manejar_comando, mock_autenticar):
        self.mock_conexion.recv.side_effect = [
            b"testuser\n",
            b"password123\n",
            b"LISTAR\n",
            b"SALIR\n"
        ]
        mock_autenticar.return_value = (1, "lectura")
        mock_manejar_comando.return_value = "archivo1.txt\narchivo2.txt"
        manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
        self.mock_conexion.sendall.assert_any_call(b"\xf0\x9f\x8c\x8d Bienvenido al server de archivos seguro.\n")
        mock_autenticar.assert_called_once_with("testuser", "password123")
        mock_manejar_comando.assert_called_once_with("LISTAR", self.directorio_base, 1)
        self.mock_conexion.sendall.assert_any_call(b"\xf0\x9f\x93\x84 archivo1.txt\narchivo2.txt\n")
        self.mock_conexion.close.assert_called_once()

    @patch('server.seguridad.autenticar_usuario_en_servidor')
    def test_manejar_cliente_autenticacion_fallida(self, mock_autenticar):
        self.mock_conexion.recv.side_effect = [
            b"testuser\n",
            b"wrongpassword\n",
            b"testuser\n",
            b"password123\n",
            b"SALIR\n"
        ]
        mock_autenticar.side_effect = [None, (1, "lectura")]
        manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
        self.assertEqual(mock_autenticar.call_count, 2)
        self.mock_conexion.sendall.assert_any_call(b"\xe2\x9d\x8c Credenciales inv\xc3\xa1lidas. Intenta nuevamente.\n")
        self.mock_conexion.sendall.assert_any_call(b"\xe2\x9c\x85 Autenticaci\xc3\xb3n exitosa! Permisos: lectura\n")

    @patch('socket.socket')
    @patch('ssl.create_default_context')
    @patch('socket.getaddrinfo')
    def test_iniciar_servidor(self, mock_getaddrinfo, mock_ssl_context, mock_socket):
        # Mock para simplificar el test usando solo IPv4
        # Nota: La implementación real en server/servidor.py soporta tanto IPv4 como IPv6 usando socket.AF_UNSPEC
        mock_sockaddr = ('127.0.0.1', 5050)
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, '', mock_sockaddr)]
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.accept.side_effect = [
            (MagicMock(), ('127.0.0.1', 12345)),
            Exception("Test exception to break the loop")
        ]
        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs'):
                try:
                    iniciar_servidor('127.0.0.1', 5050, self.directorio_base)
                except Exception as e:
                    self.assertEqual(str(e), "Test exception to break the loop")
                mock_sock.bind.assert_called_once_with(mock_sockaddr)
                mock_sock.listen.assert_called_once_with(5)
                mock_sock.accept.assert_called()
                mock_ssl_context.assert_called_once_with(ssl.Purpose.CLIENT_AUTH)
                mock_context.load_cert_chain.assert_called_once()

    @patch('server.seguridad.registrar_usuario')
    def test_manejar_cliente_registro_exitoso(self, mock_registrar):
        self.mock_conexion.recv.side_effect = [
            b"REGISTRAR newuser password123\n",
            b"SALIR\n"
        ]
        mock_registrar.side_effect = lambda u, p: "✅ Usuario registrado exitosamente."
        with patch('server.seguridad.autenticar_usuario_en_servidor') as mock_autenticar:
            mock_autenticar.return_value = (1, "lectura")
            manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
            mock_registrar.assert_called_once_with("newuser", "password123")
            self.mock_conexion.sendall.assert_any_call("✅ Usuario registrado exitosamente.\n".encode('utf-8'))

    @patch('server.seguridad.registrar_usuario')
    def test_manejar_cliente_registro_fallido(self, mock_registrar):
        self.mock_conexion.recv.side_effect = [
            b"REGISTRAR existinguser password123\n",
            b"SALIR\n"
        ]
        mock_registrar.side_effect = lambda u, p: "✅ Usuario registrado exitosamente." if u == "newuser" else "❌ Error al registrar usuario: UNIQUE constraint failed"
        with patch('server.seguridad.autenticar_usuario_en_servidor') as mock_autenticar:
            mock_autenticar.return_value = (1, "lectura")
            manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
            mock_registrar.assert_called_once_with("existinguser", "password123")
            self.mock_conexion.sendall.assert_any_call("❌ Error al registrar usuario: UNIQUE constraint failed\n".encode('utf-8'))
            calls = [call[0][0] for call in self.mock_conexion.sendall.call_args_list]
            self.assertNotIn("Ahora inicia sesión con tu nuevo usuario".encode('utf-8'), calls)


if __name__ == '__main__':
    unittest.main()
