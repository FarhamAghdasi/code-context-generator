# utils/helpers.py
"""Helper functions for size formatting, path validation, and input handling."""

import os
import platform
import sys
from colorama import Fore, Style


def validate_path(folder_path):
    """Validate that the folder path exists and is a directory."""
    if not os.path.exists(folder_path):
        raise ValueError(f"Path does not exist: {folder_path}")
    if not os.path.isdir(folder_path):
        raise ValueError(f"Path is not a directory: {folder_path}")
    return os.path.abspath(folder_path)


def get_folder_size(folder_path):
    """Calculate total size of folder in bytes."""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    except Exception:
        pass
    return total


def format_size(bytes_size):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def get_size_color(bytes_size):
    """Get color based on file/folder size."""
    mb = bytes_size / (1024 * 1024)
    if mb > 10:
        return Fore.RED
    elif mb > 5:
        return Fore.YELLOW
    else:
        return Fore.GREEN


def getch():
    """Get a single character from standard input - works on Windows, Linux, and macOS."""
    if platform.system() == 'Windows':
        import msvcrt
        char = msvcrt.getch()
        # Check for special keys (arrows, function keys, etc.)
        if char in (b'\x00', b'\xe0'):  # Special key prefix
            char = msvcrt.getch()  # Get the actual key code
            # Map Windows arrow key codes
            key_map = {
                b'H': 'UP',      # Up arrow
                b'P': 'DOWN',    # Down arrow
                b'K': 'LEFT',    # Left arrow
                b'M': 'RIGHT',   # Right arrow
            }
            return key_map.get(char, char.decode('utf-8', errors='ignore'))
        else:
            try:
                return char.decode('utf-8', errors='ignore')
            except:
                return ''
    else:
        # Linux/macOS handling
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            
            # Check for escape sequences (arrow keys)
            if ch == '\x1b':  # ESC
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    # Map Unix arrow key codes
                    key_map = {
                        'A': 'UP',
                        'B': 'DOWN',
                        'C': 'RIGHT',
                        'D': 'LEFT'
                    }
                    return key_map.get(ch3, ch3)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def select_from_list(items, title="Select an option", multi_select=False):
    """Interactive list selection with arrow keys - works on all platforms."""
    if not items:
        return None
        
    current = 0
    selected = set() if multi_select else None
    
    while True:
        # Clear screen
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
        if multi_select:
            print(f"{Fore.YELLOW}Use ↑↓ to navigate, SPACE to select, ENTER to confirm, Q to quit{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Use ↑↓ to navigate, ENTER to select, Q to quit{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
        
        # Display items
        for idx, item in enumerate(items):
            prefix = "> " if idx == current else "  "
            
            if multi_select:
                checkbox = "[X]" if idx in selected else "[ ]"
                marker = f"{checkbox} "
            else:
                marker = ""
            
            if idx == current:
                print(f"{Fore.GREEN}{prefix}{marker}{item}{Style.RESET_ALL}")
            elif multi_select and idx in selected:
                print(f"{Fore.CYAN}{prefix}{marker}{item}{Style.RESET_ALL}")
            else:
                print(f"{prefix}{marker}{item}")
        
        # Get user input
        key = getch()
        
        # Handle key presses
        if key == 'UP':
            current = (current - 1) % len(items)
        elif key == 'DOWN':
            current = (current + 1) % len(items)
        elif key in ['\r', '\n']:  # Enter
            if multi_select:
                return [items[i] for i in sorted(selected)] if selected else []
            else:
                return items[current]
        elif key == ' ' and multi_select:  # Space for multi-select
            if current in selected:
                selected.remove(current)
            else:
                selected.add(current)
        elif key.lower() == 'q':
            return None
        elif key == '\x1b':  # ESC key
            return None