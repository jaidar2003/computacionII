import sys
import os
import unittest
import warnings

# Ignorar DeprecationWarnings durante los tests
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Agregar path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tareas.celery import verificar_integridad_y_virus

class TestTareasCelery(unittest.TestCase):

    def test_archivo_valido(self):
        ruta = "test_archivo_seguro.txt"
        with open(ruta, "w") as f:
            f.write("Archivo normal")

        resultado = verificar_integridad_y_virus.delay(ruta)
        final = resultado.get(timeout=10)

        self.assertEqual(final["estado"], "ok")
        self.assertIn("verificado", final["detalle"].lower())
        os.remove(ruta)

    def test_archivo_malicioso(self):
        ruta = "test_malware.exe"
        with open(ruta, "w") as f:
            f.write("Contenido sospechoso")

        resultado = verificar_integridad_y_virus.delay(ruta)
        final = resultado.get(timeout=10)

        self.assertEqual(final["estado"], "inseguro")
        self.assertIn("malicioso", final["detalle"].lower())
        os.remove(ruta)

    def test_archivo_inexistente(self):
        ruta = "no_existe.txt"
        resultado = verificar_integridad_y_virus.delay(ruta)
        final = resultado.get(timeout=10)

        self.assertEqual(final["estado"], "error")
        self.assertIn("no encontrado", final["detalle"].lower())

if __name__ == "__main__":
    unittest.main()
