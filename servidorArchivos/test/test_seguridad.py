import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from servidor.seguridad import autenticar_usuario_en_servidor, registrar_usuario

class TestSeguridad(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for any files needed
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    @patch('server.seguridad.autenticar_usuario')
    def test_autenticar_usuario_en_servidor_exito(self, mock_autenticar):
        """Test successful user authentication"""
        # Mock the database authentication to return a successful result
        mock_autenticar.return_value = (1, "lectura")
        
        # Call the function
        result = autenticar_usuario_en_servidor("testuser", "password123")
        
        # Check that the database function was called with correct parameters
        mock_autenticar.assert_called_once_with("testuser", "password123")
        
        # Check the result
        self.assertEqual(result, (1, "lectura"))
    
    @patch('server.seguridad.autenticar_usuario')
    def test_autenticar_usuario_en_servidor_fallo(self, mock_autenticar):
        """Test failed user authentication"""
        # Mock the database authentication to return None (authentication failed)
        mock_autenticar.return_value = None
        
        # Call the function
        result = autenticar_usuario_en_servidor("testuser", "wrongpassword")
        
        # Check that the database function was called with correct parameters
        mock_autenticar.assert_called_once_with("testuser", "wrongpassword")
        
        # Check the result
        self.assertIsNone(result)
    
    @patch('server.seguridad.db_registrar_usuario')
    def test_registrar_usuario_exito(self, mock_registrar):
        """Test successful user registration"""
        # Mock the database registration to return a successful result
        mock_registrar.return_value = "✅ Usuario registrado exitosamente."
        
        # Call the function
        result = registrar_usuario("newuser", "password123")
        
        # Check that the password was hashed before being passed to the database function
        # The first argument should be the username, and the second should be the hashed password
        args, _ = mock_registrar.call_args
        self.assertEqual(args[0], "newuser")
        self.assertNotEqual(args[1], "password123")  # Password should be hashed
        self.assertEqual(args[2], "lectura")  # Default permission
        
        # Check the result
        self.assertEqual(result, "✅ Usuario registrado exitosamente.")
    
    @patch('server.seguridad.db_registrar_usuario')
    def test_registrar_usuario_fallo(self, mock_registrar):
        """Test failed user registration"""
        # Mock the database registration to return an error
        mock_registrar.return_value = "❌ Error al registrar usuario: UNIQUE constraint failed"
        
        # Call the function
        result = registrar_usuario("existinguser", "password123")
        
        # Check the result
        self.assertEqual(result, "❌ Error al registrar usuario: UNIQUE constraint failed")
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        # Call the function with a known password
        with patch('server.seguridad.db_registrar_usuario') as mock_registrar:
            mock_registrar.return_value = "✅ Usuario registrado exitosamente."
            registrar_usuario("testuser", "password123")
            
            # Get the hashed password that was passed to the database function
            args, _ = mock_registrar.call_args
            hashed_password = args[1]
            
            # Verify it's not the original password
            self.assertNotEqual(hashed_password, "password123")
            
            # Verify it's a SHA-256 hash (64 characters)
            self.assertEqual(len(hashed_password), 64)

if __name__ == '__main__':
    unittest.main()