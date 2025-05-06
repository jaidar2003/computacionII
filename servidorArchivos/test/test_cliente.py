import unittest
import os
import sys
import tempfile
import socket
import ssl
from unittest.mock import patch, MagicMock, Mock, call

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from servidor.cliente import iniciar_cliente

class TestCliente(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for any files needed
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Mock input/output
        self.patcher_input = patch('builtins.input')
        self.mock_input = self.patcher_input.start()
        
        self.patcher_print = patch('builtins.print')
        self.mock_print = self.patcher_print.start()
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        
        # Stop patchers
        self.patcher_input.stop()
        self.patcher_print.stop()
    
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_login_exitoso(self, mock_ssl_context, mock_create_connection):
        """Test successful login and command execution"""
        # Mock user input
        self.mock_input.side_effect = [
            "1",  # Select login option
            "testuser",  # Username
            "password123",  # Password
            "LISTAR",  # Command
            "SALIR"  # Exit command
        ]
        
        # Mock SSL connection
        mock_ssl_sock = MagicMock()
        mock_ssl_sock.recv.side_effect = [
            b"Welcome message",  # Welcome message
            b"\xe2\x9c\x85 Autenticaci\xc3\xb3n exitosa! Permisos: lectura",  # Authentication success
            b"archivo1.txt\narchivo2.txt"  # Command response
        ]
        
        # Mock SSL context
        mock_context = MagicMock()
        mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        mock_ssl_context.return_value = mock_context
        
        # Mock socket connection
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock
        
        # Call the function
        iniciar_cliente("localhost", 5050)
        
        # Check that the socket was created with the correct parameters
        mock_create_connection.assert_called_once_with(("localhost", 5050))
        
        # Check that the SSL context was created
        mock_ssl_context.assert_called_once()
        
        # Check that the socket was wrapped with SSL
        mock_context.wrap_socket.assert_called_once_with(mock_sock, server_hostname="localhost")
        
        # Check that the username and password were sent
        mock_ssl_sock.sendall.assert_any_call(b"testuser\n")
        mock_ssl_sock.sendall.assert_any_call(b"password123\n")
        
        # Check that the command was sent
        mock_ssl_sock.sendall.assert_any_call(b"LISTAR\n")
        
        # Check that the exit command was sent
        mock_ssl_sock.sendall.assert_any_call(b"SALIR\n")
    
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_registro_exitoso(self, mock_ssl_context, mock_create_connection):
        """Test successful registration"""
        # Mock user input
        self.mock_input.side_effect = [
            "2",  # Select registration option
            "newuser",  # New username
            "newpassword",  # New password
            "3"  # Exit option
        ]
        
        # Mock SSL connection
        mock_ssl_sock = MagicMock()
        mock_ssl_sock.recv.side_effect = [
            b"Welcome message",  # Welcome message
            b"\xe2\x9c\x85 Usuario registrado exitosamente."  # Registration success
        ]
        
        # Mock SSL context
        mock_context = MagicMock()
        mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        mock_ssl_context.return_value = mock_context
        
        # Mock socket connection
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock
        
        # Call the function
        iniciar_cliente("localhost", 5050)
        
        # Check that the registration command was sent
        mock_ssl_sock.sendall.assert_any_call(b"REGISTRAR newuser newpassword\n")
    
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_registro_fallido(self, mock_ssl_context, mock_create_connection):
        """Test failed registration"""
        # Mock user input
        self.mock_input.side_effect = [
            "2",  # Select registration option
            "existinguser",  # Existing username
            "password123",  # Password
            "3"  # Exit option
        ]
        
        # Mock SSL connection
        mock_ssl_sock = MagicMock()
        mock_ssl_sock.recv.side_effect = [
            b"Welcome message",  # Welcome message
            b"\xe2\x9d\x8c Error al registrar usuario: UNIQUE constraint failed"  # Registration failure
        ]
        
        # Mock SSL context
        mock_context = MagicMock()
        mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        mock_ssl_context.return_value = mock_context
        
        # Mock socket connection
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock
        
        # Call the function
        iniciar_cliente("localhost", 5050)
        
        # Check that the registration command was sent
        mock_ssl_sock.sendall.assert_any_call(b"REGISTRAR existinguser password123\n")
        
        # Check that the error message was printed
        self.mock_print.assert_any_call("\n❌ Error al registrar usuario: UNIQUE constraint failed")
    
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_login_fallido(self, mock_ssl_context, mock_create_connection):
        """Test failed login"""
        # Mock user input
        self.mock_input.side_effect = [
            "1",  # Select login option
            "testuser",  # Username
            "wrongpassword",  # Wrong password
            "3"  # Exit option
        ]
        
        # Mock SSL connection
        mock_ssl_sock = MagicMock()
        mock_ssl_sock.recv.side_effect = [
            b"Welcome message",  # Welcome message
            b"\xe2\x9d\x8c Credenciales inv\xc3\xa1lidas. Intenta nuevamente."  # Authentication failure
        ]
        
        # Mock SSL context
        mock_context = MagicMock()
        mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        mock_ssl_context.return_value = mock_context
        
        # Mock socket connection
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock
        
        # Call the function
        iniciar_cliente("localhost", 5050)
        
        # Check that the username and password were sent
        mock_ssl_sock.sendall.assert_any_call(b"testuser\n")
        mock_ssl_sock.sendall.assert_any_call(b"wrongpassword\n")
        
        # Check that the error message was printed
        self.mock_print.assert_any_call("\n❌ Credenciales inválidas. Intenta nuevamente.")
    
    @patch('socket.create_connection', side_effect=socket.error("Connection refused"))
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_error_conexion(self, mock_ssl_context, mock_create_connection):
        """Test connection error"""
        # Call the function
        iniciar_cliente("localhost", 5050)
        
        # Check that the error message was printed
        self.mock_print.assert_any_call("\n❌ Error de conexión: Connection refused")

if __name__ == '__main__':
    unittest.main()