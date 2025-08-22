#!/usr/bin/env python3
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Change working directory to the CLI directory
os.chdir(os.path.join(os.path.dirname(__file__), 'final', 'servidorArchivos'))

# Import and run the CLI
from final.servidorArchivos.cli.menu_cli import main

if __name__ == '__main__':
    # Pass all command line arguments to the CLI
    sys.argv = [sys.argv[0]] + sys.argv[1:]
    main()