import unittest
import os
import sys
import sqlite3
import tempfile

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from base_datos.db import crear_tablas, registrar_usuario, autenticar_usuario, registrar_log

class TestDB(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        
        # Patch the DB_PATH to use our temporary database
        self.original_db_path = os.environ.get('DB_PATH')
        os.environ['DB_PATH'] = self.temp_db_path
        
        # Create the tables in the test database
        crear_tablas()
    
    def tearDown(self):
        # Close and remove the temporary database
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)
        
        # Restore the original DB_PATH
        if self.original_db_path:
            os.environ['DB_PATH'] = self.original_db_path
        else:
            os.environ.pop('DB_PATH', None)
    
    def test_crear_tablas(self):
        """Test that tables are created correctly"""
        # Connect to the database and check if tables exist
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        # Check usuarios table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        self.assertIsNotNone(cursor.fetchone(), "usuarios table should exist")
        
        # Check logs table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        self.assertIsNotNone(cursor.fetchone(), "logs table should exist")
        
        conn.close()
    
    def test_registrar_usuario(self):
        """Test user registration"""
        # Register a test user
        result = registrar_usuario("testuser", "password123", "lectura")
        self.assertEqual(result, "✅ Usuario registrado exitosamente.")
        
        # Try to register the same user again (should fail)
        result = registrar_usuario("testuser", "password123", "lectura")
        self.assertTrue(result.startswith("❌ Error al registrar usuario"))
        
        # Check if the user exists in the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username, permisos FROM usuarios WHERE username = ?", ("testuser",))
        user = cursor.fetchone()
        self.assertIsNotNone(user, "User should exist in the database")
        self.assertEqual(user[0], "testuser", "Username should match")
        self.assertEqual(user[1], "lectura", "Permissions should match")
        conn.close()
    
    def test_autenticar_usuario(self):
        """Test user authentication"""
        # Register a test user
        registrar_usuario("authuser", "password123", "lectura")
        
        # Test successful authentication
        user = autenticar_usuario("authuser", "password123")
        self.assertIsNotNone(user, "Authentication should succeed")
        self.assertEqual(user[1], "lectura", "Permissions should match")
        
        # Test failed authentication with wrong password
        user = autenticar_usuario("authuser", "wrongpassword")
        self.assertIsNone(user, "Authentication should fail with wrong password")
        
        # Test failed authentication with non-existent user
        user = autenticar_usuario("nonexistentuser", "password123")
        self.assertIsNone(user, "Authentication should fail with non-existent user")
    
    def test_registrar_log(self):
        """Test log registration"""
        # Register a test user
        registrar_usuario("loguser", "password123", "lectura")
        
        # Get the user ID
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", ("loguser",))
        user_id = cursor.fetchone()[0]
        
        # Register a log
        registrar_log(user_id, "TEST_ACTION", "test_file.txt")
        
        # Check if the log exists
        cursor.execute("SELECT usuario_id, accion, archivo FROM logs WHERE usuario_id = ?", (user_id,))
        log = cursor.fetchone()
        self.assertIsNotNone(log, "Log should exist in the database")
        self.assertEqual(log[0], user_id, "User ID should match")
        self.assertEqual(log[1], "TEST_ACTION", "Action should match")
        self.assertEqual(log[2], "test_file.txt", "File should match")
        conn.close()

if __name__ == '__main__':
    unittest.main()