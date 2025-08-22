import os
import sys
from colorama import init, Fore, Style, Back

# Initialize colorama
init(autoreset=True)

# Color constants
SUCCESS = Fore.GREEN
ERROR = Fore.RED
WARNING = Fore.YELLOW
INFO = Fore.BLUE
HEADER = Fore.MAGENTA
BOLD = Style.BRIGHT
RESET = Style.RESET_ALL
HIGHLIGHT = Back.WHITE + Fore.BLACK

def format_success(message):
    """Format a success message"""
    return f"{SUCCESS}{BOLD}✅ {message}{RESET}"

def format_error(message):
    """Format an error message"""
    return f"{ERROR}{BOLD}❌ {message}{RESET}"

def format_warning(message):
    """Format a warning message"""
    return f"{WARNING}{BOLD}⚠️ {message}{RESET}"

def format_info(message):
    """Format an info message"""
    return f"{INFO}ℹ️ {message}{RESET}"

def format_header(message):
    """Format a header message"""
    return f"\n{HEADER}{BOLD}{message}{RESET}"

def format_highlight(message):
    """Format a highlighted message"""
    return f"{HIGHLIGHT}{message}{RESET}"

def print_success(message):
    """Print a success message"""
    print(format_success(message))

def print_error(message):
    """Print an error message"""
    print(format_error(message))

def print_warning(message):
    """Print a warning message"""
    print(format_warning(message))

def print_info(message):
    """Print an info message"""
    print(format_info(message))

def print_header(message):
    """Print a header message"""
    print(format_header(message))

def print_table_header(columns, widths):
    """Print a table header with the given columns and widths"""
    header = ""
    separator = ""
    
    for i, col in enumerate(columns):
        header += f"{col:{widths[i]}} "
        separator += "-" * widths[i] + " "
    
    print(f"{BOLD}{header.strip()}{RESET}")
    print(separator.strip())

def print_table_row(values, widths):
    """Print a table row with the given values and widths"""
    row = ""
    
    for i, val in enumerate(values):
        row += f"{val:{widths[i]}} "
    
    print(row.strip())

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_size():
    """Get the terminal size"""
    return os.get_terminal_size()