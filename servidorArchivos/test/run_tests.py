import unittest
import os
import sys
from colorama import Fore, Style, init
import io
import logging

# Inicializar colorama para colores en consola
init(autoreset=True)

# Asegurar que el path al proyecto esté en sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Silenciar logs en modo test
logging.getLogger().setLevel(logging.CRITICAL)
# Activar variable de entorno para modo test
os.environ["TEST_MODE"] = "1"

def run_tests():
    test_dir = os.path.join(os.path.dirname(__file__))
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py')

    # Capturar salida para mostrar resumen limpio
    buffer = io.StringIO()
    runner = unittest.TextTestRunner(stream=buffer, verbosity=2)
    result = runner.run(suite)

    # Mostrar salida del runner
    print(buffer.getvalue())

    # Mostrar resumen bonito
    total_tests = result.testsRun
    total_errors = len(result.errors)
    total_failures = len(result.failures)
    total_successes = total_tests - total_errors - total_failures

    print("\n" + "="*50)
    print(f"{Fore.CYAN}Resumen de Resultados:")
    print(f"{Fore.GREEN}  ✅ {total_successes} exitosos")
    print(f"{Fore.RED}  ❌ {total_failures} fallos")
    print(f"{Fore.YELLOW}  ⚠️  {total_errors} errores")
    print("="*50 + "\n")

    if result.wasSuccessful():
        exit(0)
    else:
        exit(1)

if __name__ == '__main__':
    run_tests()
