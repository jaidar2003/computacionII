import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.comandos import manejar_comando, listar_archivos, crear_archivo, eliminar_archivo, renombrar_archivo

class TestComandos(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for file operations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directorio_base = self.temp_dir.name
        self.usuario_id = 1  # Mock user ID for testing

        # Create some test files
        self.test_files = ["archivo1.txt", "archivo2.txt", "archivo3.txt"]
        for file_name in self.test_files:
            with open(os.path.join(self.directorio_base, file_name), 'w') as f:
                f.write(f"Contenido de prueba para {file_name}")

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_listar_archivos(self):
        """Test listing files"""
        # Call the function
        result = listar_archivos(self.directorio_base)

        # Check that all test files are in the result
        for file_name in self.test_files:
            self.assertIn(file_name, result)

    def test_listar_archivos_vacio(self):
        """Test listing files in an empty directory"""
        # Create a new empty directory
        empty_dir = tempfile.TemporaryDirectory()

        # Call the function
        result = listar_archivos(empty_dir.name)

        # Check the result
        self.assertEqual(result, "📂 No hay archivos en el servidor.")

        # Clean up
        empty_dir.cleanup()

    @patch('server.comandos.verificar_integridad_y_virus')
    def test_crear_archivo(self, mock_verificar):
        """Test creating a file without hash"""
        # Mock the verificar_integridad_y_virus.delay function
        mock_verificar.delay.return_value = None

        # Call the function
        nuevo_archivo = "nuevo_archivo.txt"
        result = crear_archivo(self.directorio_base, nuevo_archivo)

        # Check the result
        self.assertEqual(result, f"✅ Archivo '{nuevo_archivo}' creado y enviado para verificación.")

        # Check that the file was created
        self.assertTrue(os.path.exists(os.path.join(self.directorio_base, nuevo_archivo)))

        # Check that the verification was called with None as the hash parameter
        mock_verificar.delay.assert_called_once_with(os.path.join(self.directorio_base, nuevo_archivo), None)

    @patch('server.comandos.verificar_integridad_y_virus')
    def test_crear_archivo_con_hash(self, mock_verificar):
        """Test creating a file with hash"""
        # Mock the verificar_integridad_y_virus.delay function
        mock_verificar.delay.return_value = None

        # Call the function
        nuevo_archivo = "nuevo_archivo_hash.txt"
        hash_esperado = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        result = crear_archivo(self.directorio_base, nuevo_archivo, hash_esperado)

        # Check the result
        self.assertEqual(result, f"✅ Archivo '{nuevo_archivo}' creado y enviado para verificación con hash.")

        # Check that the file was created
        self.assertTrue(os.path.exists(os.path.join(self.directorio_base, nuevo_archivo)))

        # Check that the verification was called with the hash
        mock_verificar.delay.assert_called_once_with(os.path.join(self.directorio_base, nuevo_archivo), hash_esperado)

    def test_crear_archivo_existente(self):
        """Test creating a file that already exists"""
        # Call the function with an existing file name
        result = crear_archivo(self.directorio_base, self.test_files[0])

        # Check the result
        self.assertEqual(result, f"⚠️ El archivo '{self.test_files[0]}' ya existe.")

    def test_eliminar_archivo(self):
        """Test deleting a file"""
        # Call the function
        result = eliminar_archivo(self.directorio_base, self.test_files[0])

        # Check the result
        self.assertEqual(result, f"🗑️ Archivo '{self.test_files[0]}' eliminado.")

        # Check that the file was deleted
        self.assertFalse(os.path.exists(os.path.join(self.directorio_base, self.test_files[0])))

    def test_eliminar_archivo_inexistente(self):
        """Test deleting a file that doesn't exist"""
        # Call the function with a non-existent file name
        archivo_inexistente = "archivo_inexistente.txt"
        result = eliminar_archivo(self.directorio_base, archivo_inexistente)

        # Check the result
        self.assertEqual(result, f"⚠️ Archivo '{archivo_inexistente}' no encontrado.")

    def test_renombrar_archivo(self):
        """Test renaming a file"""
        # Call the function
        nuevo_nombre = "archivo_renombrado.txt"
        result = renombrar_archivo(self.directorio_base, self.test_files[0], nuevo_nombre)

        # Check the result
        self.assertEqual(result, f"✏️ Archivo '{self.test_files[0]}' renombrado a '{nuevo_nombre}'.")

        # Check that the file was renamed
        self.assertFalse(os.path.exists(os.path.join(self.directorio_base, self.test_files[0])))
        self.assertTrue(os.path.exists(os.path.join(self.directorio_base, nuevo_nombre)))

    def test_renombrar_archivo_inexistente(self):
        """Test renaming a file that doesn't exist"""
        # Call the function with a non-existent file name
        archivo_inexistente = "archivo_inexistente.txt"
        nuevo_nombre = "archivo_renombrado.txt"
        result = renombrar_archivo(self.directorio_base, archivo_inexistente, nuevo_nombre)

        # Check the result
        self.assertEqual(result, f"⚠️ Archivo '{archivo_inexistente}' no encontrado.")

    @patch('server.comandos.listar_archivos')
    def test_manejar_comando_listar(self, mock_listar):
        """Test handling LISTAR command"""
        # Mock the listar_archivos function
        mock_listar.return_value = "archivo1.txt\narchivo2.txt\narchivo3.txt"

        # Call the function
        result = manejar_comando("LISTAR", self.directorio_base)

        # Check that the listar_archivos function was called with correct parameters
        mock_listar.assert_called_once_with(self.directorio_base)

        # Check the result
        self.assertEqual(result, "archivo1.txt\narchivo2.txt\narchivo3.txt")

    @patch('server.comandos.crear_archivo')
    def test_manejar_comando_crear(self, mock_crear):
        """Test handling CREAR command"""
        # Mock the crear_archivo function
        mock_crear.return_value = "✅ Archivo 'nuevo_archivo.txt' creado y enviado para verificación."

        # Call the function
        result = manejar_comando("CREAR nuevo_archivo.txt", self.directorio_base)

        # Check that the crear_archivo function was called with correct parameters
        mock_crear.assert_called_once_with(self.directorio_base, "nuevo_archivo.txt")

        # Check the result
        self.assertEqual(result, "✅ Archivo 'nuevo_archivo.txt' creado y enviado para verificación.")

    @patch('server.comandos.eliminar_archivo')
    def test_manejar_comando_eliminar(self, mock_eliminar):
        """Test handling ELIMINAR command"""
        # Mock the eliminar_archivo function
        mock_eliminar.return_value = "🗑️ Archivo 'archivo1.txt' eliminado."

        # Call the function
        result = manejar_comando("ELIMINAR archivo1.txt", self.directorio_base)

        # Check that the eliminar_archivo function was called with correct parameters
        mock_eliminar.assert_called_once_with(self.directorio_base, "archivo1.txt")

        # Check the result
        self.assertEqual(result, "🗑️ Archivo 'archivo1.txt' eliminado.")

    @patch('server.comandos.renombrar_archivo')
    def test_manejar_comando_renombrar(self, mock_renombrar):
        """Test handling RENOMBRAR command"""
        # Mock the renombrar_archivo function
        mock_renombrar.return_value = "✏️ Archivo 'archivo1.txt' renombrado a 'archivo_renombrado.txt'."

        # Call the function
        result = manejar_comando("RENOMBRAR archivo1.txt archivo_renombrado.txt", self.directorio_base)

        # Check that the renombrar_archivo function was called with correct parameters
        mock_renombrar.assert_called_once_with(self.directorio_base, "archivo1.txt", "archivo_renombrado.txt")

        # Check the result
        self.assertEqual(result, "✏️ Archivo 'archivo1.txt' renombrado a 'archivo_renombrado.txt'.")

    def test_manejar_comando_invalido(self):
        """Test handling invalid command"""
        # Call the function with an invalid command
        result = manejar_comando("COMANDO_INVALIDO", self.directorio_base)

        # Check the result
        self.assertEqual(result, "❌ Comando no reconocido o argumentos inválidos.")

if __name__ == '__main__':
    unittest.main()
