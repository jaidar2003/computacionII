import unittest
import os
import sys
import tempfile
import socket
import ssl
from unittest.mock import patch, MagicMock, Mock, call

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.cliente import iniciar_cliente, calcular_hash_archivo

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

    def test_calcular_hash_archivo(self):
        """Test calculating the hash of a file"""
        # Create a test file with known content
        test_file_path = os.path.join(self.temp_dir.name, "test_hash.txt")
        test_content = "This is a test file for hash calculation."
        with open(test_file_path, 'w') as f:
            f.write(test_content)

        # Calculate the hash
        hash_result = calcular_hash_archivo(test_file_path)

        # Calculate the expected hash
        import hashlib
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()

        # Check that the hash is correct
        self.assertEqual(hash_result, expected_hash)

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
            b"Options message",  # Options message
            b"Username prompt",  # Username prompt
            b"Password prompt",  # Password prompt
            b"\xe2\x9c\x85 Autenticaci\xc3\xb3n exitosa! Permisos: lectura",  # Authentication success
            b"Command prompt",  # Command prompt
            b"archivo1.txt\narchivo2.txt",  # Command response
            b"Command prompt"  # Command prompt for SALIR
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

        # Check that the option, username, password, and commands were sent
        expected_calls = [
            call(b"1\n"),  # Option
            call(b"testuser\n"),  # Username
            call(b"password123\n"),  # Password
            call(b"LISTAR\n"),  # Command
            call(b"SALIR\n")  # Exit command
        ]
        mock_ssl_sock.sendall.assert_has_calls(expected_calls, any_order=False)

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
            b"Options message",  # Options message
            b"\xe2\x9c\x85 Usuario registrado exitosamente.",  # Registration success
            b"Options message"  # Options message for exit
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

        # Check that the registration option and combined registration command were sent
        expected_calls = [
            call(b"2\n"),  # Registration option
            call(b"REGISTRAR newuser newpassword\n"),  # Combined registration command
        ]
        mock_ssl_sock.sendall.assert_has_calls(expected_calls, any_order=False)

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
            b"Options message",  # Options message
            b"\xe2\x9d\x8c Error al registrar usuario: UNIQUE constraint failed",  # Registration failure
            b"Options message"  # Options message for exit
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

        # Check that the registration option, combined registration command, and exit option were sent
        expected_calls = [
            call(b"2\n"),  # Registration option
            call(b"REGISTRAR existinguser password123\n"),  # Combined registration command
            call(b"3\n")  # Exit option
        ]
        mock_ssl_sock.sendall.assert_has_calls(expected_calls, any_order=False)

        # Check that the error message was printed - using a partial match to avoid encoding issues
        found = False
        for call_args in self.mock_print.call_args_list:
            if "Error al registrar usuario" in call_args[0][0] and "UNIQUE constraint failed" in call_args[0][0]:
                found = True
                break
        self.assertTrue(found, "Expected error message about registration failure not found")

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
            b"Options message",  # Options message
            b"Username prompt",  # Username prompt
            b"Password prompt",  # Password prompt
            b"\xe2\x9d\x8c Credenciales inv\xc3\xa1lidas. Intenta nuevamente.",  # Authentication failure
            b"Options message"  # Options message for exit
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

        # Check that the login option, username, password, and exit option were sent
        expected_calls = [
            call(b"1\n"),  # Login option
            call(b"testuser\n"),  # Username
            call(b"wrongpassword\n"),  # Wrong password
            call(b"3\n")  # Exit option
        ]
        mock_ssl_sock.sendall.assert_has_calls(expected_calls, any_order=False)

        # Check that the error message was printed - using a partial match to avoid encoding issues
        found = False
        for call_args in self.mock_print.call_args_list:
            if "Credenciales" in call_args[0][0] and "lidas" in call_args[0][0]:
                found = True
                break
        self.assertTrue(found, "Expected error message about invalid credentials not found")

    @patch('os.path.exists')
    @patch('server.cliente.calcular_hash_archivo')
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_crear_con_hash(self, mock_ssl_context, mock_create_connection, mock_calcular_hash, mock_exists):
        """Test creating a file with hash"""
        # Mock file existence and hash calculation
        mock_exists.return_value = True
        mock_calcular_hash.return_value = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        # Mock user input
        self.mock_input.side_effect = [
            "1",  # Select login option
            "testuser",  # Username
            "password123",  # Password
            "CREAR archivo.txt",  # CREAR command
            "/path/to/local/file.txt",  # Local file path
            "SALIR"  # Exit command
        ]

        # Mock SSL connection
        mock_ssl_sock = MagicMock()
        mock_ssl_sock.recv.side_effect = [
            b"Welcome message",  # Welcome message
            b"Options message",  # Options message
            b"Username prompt",  # Username prompt
            b"Password prompt",  # Password prompt
            b"\xe2\x9c\x85 Autenticaci\xc3\xb3n exitosa! Permisos: lectura",  # Authentication success
            b"Command prompt",  # Command prompt
            b"File created with hash",  # Command response
            b"Command prompt"  # Command prompt for SALIR
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

        # Check that the command with hash was sent
        expected_command = f"CREAR archivo.txt {mock_calcular_hash.return_value}\n".encode('utf-8')
        mock_ssl_sock.sendall.assert_any_call(expected_command)

    @patch('socket.create_connection', side_effect=ConnectionRefusedError("Connection refused"))
    @patch('ssl.create_default_context')
    def test_iniciar_cliente_error_conexion(self, mock_ssl_context, mock_create_connection):
        """Test connection error"""
        # Call the function
        iniciar_cliente("localhost", 5050)

        # Check that the error message was printed
        self.mock_print.assert_any_call("❌ No se pudo conectar al servidor localhost:5050. Asegúrate de que el servidor esté en ejecución.")

if __name__ == '__main__':
    unittest.main()
