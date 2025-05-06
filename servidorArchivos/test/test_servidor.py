import unittest
import os
import sys
import tempfile
import socket
import ssl
from unittest.mock import patch, MagicMock, Mock

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.servidor import manejar_cliente, iniciar_servidor

class TestServidor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for file operations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directorio_base = self.temp_dir.name
        
        # Mock SSL connection
        self.mock_conexion = MagicMock()
        self.mock_direccion = ('127.0.0.1', 12345)
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    @patch('server.server.autenticar_usuario_en_servidor')
    @patch('server.server.manejar_comando')
    def test_manejar_cliente_autenticacion_exitosa(self, mock_manejar_comando, mock_autenticar):
        """Test successful client authentication and command handling"""
        # Set up the mock connection to return appropriate data
        self.mock_conexion.recv.side_effect = [
            b"testuser\n",  # Username
            b"password123\n",  # Password
            b"LISTAR\n",  # Command
            b"SALIR\n"  # Exit command
        ]
        
        # Mock successful authentication
        mock_autenticar.return_value = (1, "lectura")
        
        # Mock command handling
        mock_manejar_comando.return_value = "archivo1.txt\narchivo2.txt"
        
        # Call the function
        manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
        
        # Check that the connection received the welcome message
        self.mock_conexion.sendall.assert_any_call(b"\xf0\x9f\x8c\x8d Bienvenido al server de archivos seguro.\n")
        
        # Check that authentication was called with correct parameters
        mock_autenticar.assert_called_once_with("testuser", "password123")
        
        # Check that command handling was called with correct parameters
        mock_manejar_comando.assert_called_once_with("LISTAR", self.directorio_base, 1)
        
        # Check that the connection received the command response
        self.mock_conexion.sendall.assert_any_call(b"\xf0\x9f\x93\x84 archivo1.txt\narchivo2.txt\n")
        
        # Check that the connection was closed
        self.mock_conexion.close.assert_called_once()
    
    @patch('server.server.autenticar_usuario_en_servidor')
    def test_manejar_cliente_autenticacion_fallida(self, mock_autenticar):
        """Test failed client authentication"""
        # Set up the mock connection to return appropriate data
        self.mock_conexion.recv.side_effect = [
            b"testuser\n",  # Username
            b"wrongpassword\n",  # Wrong password
            b"testuser\n",  # Username again
            b"password123\n",  # Correct password
            b"SALIR\n"  # Exit command
        ]
        
        # Mock failed authentication first, then successful
        mock_autenticar.side_effect = [None, (1, "lectura")]
        
        # Call the function
        manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
        
        # Check that authentication was called twice
        self.assertEqual(mock_autenticar.call_count, 2)
        
        # Check that the connection received the authentication failure message
        self.mock_conexion.sendall.assert_any_call(b"\xe2\x9d\x8c Credenciales inv\xc3\xa1lidas. Intenta nuevamente.\n")
        
        # Check that the connection received the authentication success message
        self.mock_conexion.sendall.assert_any_call(b"\xe2\x9c\x85 Autenticaci\xc3\xb3n exitosa! Permisos: lectura\n")
    
    @patch('server.server.registrar_usuario')
    def test_manejar_cliente_registro_exitoso(self, mock_registrar):
        """Test successful user registration"""
        # Set up the mock connection to return appropriate data
        self.mock_conexion.recv.side_effect = [
            b"REGISTRAR newuser password123\n",  # Registration command
            b"testuser\n",  # Username for login
            b"password123\n",  # Password for login
            b"SALIR\n"  # Exit command
        ]
        
        # Mock successful registration
        mock_registrar.return_value = "✅ Usuario registrado exitosamente."
        
        # Mock successful authentication after registration
        with patch('server.server.autenticar_usuario_en_servidor') as mock_autenticar:
            mock_autenticar.return_value = (1, "lectura")
            
            # Call the function
            manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
            
            # Check that registration was called with correct parameters
            mock_registrar.assert_called_once_with("newuser", "password123")
            
            # Check that the connection received the registration success message
            self.mock_conexion.sendall.assert_any_call(b"\xe2\x9c\x85 Usuario registrado exitosamente.\n")
            
            # Check that the connection received the additional message
            self.mock_conexion.sendall.assert_any_call(b"\xf0\x9f\x91\xa4 Ahora inicia sesi\xc3\xb3n con tu nuevo usuario.\n")
    
    @patch('server.server.registrar_usuario')
    def test_manejar_cliente_registro_fallido(self, mock_registrar):
        """Test failed user registration"""
        # Set up the mock connection to return appropriate data
        self.mock_conexion.recv.side_effect = [
            b"REGISTRAR existinguser password123\n",  # Registration command
            b"testuser\n",  # Username for login
            b"password123\n",  # Password for login
            b"SALIR\n"  # Exit command
        ]
        
        # Mock failed registration
        mock_registrar.return_value = "❌ Error al registrar usuario: UNIQUE constraint failed"
        
        # Mock successful authentication after registration attempt
        with patch('server.server.autenticar_usuario_en_servidor') as mock_autenticar:
            mock_autenticar.return_value = (1, "lectura")
            
            # Call the function
            manejar_cliente(self.mock_conexion, self.mock_direccion, self.directorio_base)
            
            # Check that registration was called with correct parameters
            mock_registrar.assert_called_once_with("existinguser", "password123")
            
            # Check that the connection received the registration failure message
            self.mock_conexion.sendall.assert_any_call(b"\xe2\x9d\x8c Error al registrar usuario: UNIQUE constraint failed\n")
            
            # Check that the connection did not receive the additional message
            for call in self.mock_conexion.sendall.call_args_list:
                self.assertNotIn(b"Ahora inicia sesi\xc3\xb3n con tu nuevo usuario", call[0][0])
    
    @patch('socket.socket')
    @patch('ssl.create_default_context')
    @patch('socket.getaddrinfo')
    def test_iniciar_servidor(self, mock_getaddrinfo, mock_ssl_context, mock_socket):
        """Test server initialization"""
        # Mock getaddrinfo to return a valid address
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('127.0.0.1', 5050))]
        
        # Mock SSL context
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        
        # Mock socket
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        # Mock socket.accept to raise an exception after first call to break the infinite loop
        mock_sock.accept.side_effect = [
            (MagicMock(), ('127.0.0.1', 12345)),
            Exception("Test exception to break the loop")
        ]
        
        # Mock os.path.exists to return True for certificate paths
        with patch('os.path.exists', return_value=True):
            # Mock os.makedirs to avoid creating directories
            with patch('os.makedirs'):
                # Call the function and catch the expected exception
                try:
                    iniciar_servidor('127.0.0.1', 5050, self.directorio_base)
                except Exception as e:
                    self.assertEqual(str(e), "Test exception to break the loop")
                
                # Check that the socket was bound to the correct address
                mock_sock.bind.assert_called_once_with(('127.0.0.1', 5050))
                
                # Check that the socket was set to listen
                mock_sock.listen.assert_called_once_with(5)
                
                # Check that accept was called
                mock_sock.accept.assert_called()
                
                # Check that the SSL context was created
                mock_ssl_context.assert_called_once_with(ssl.Purpose.CLIENT_AUTH)
                
                # Check that the certificate chain was loaded
                mock_context.load_cert_chain.assert_called_once()

if __name__ == '__main__':
    unittest.main()