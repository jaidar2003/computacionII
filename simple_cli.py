#!/usr/bin/env python3
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Change working directory to the servidorArchivos directory
os.chdir(os.path.join(os.path.dirname(__file__), 'final', 'servidorArchivos'))

# Import and run the simple CLI
from final.servidorArchivos.cli.simple.simple_menu import main

if __name__ == '__main__':
    main()