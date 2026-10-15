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


# Context size thresholds (bytes) used for per-file color coding.
CONTEXT_LOW_BYTES = 16 * 1024       # < 16 KB   -> green
CONTEXT_MEDIUM_BYTES = 128 * 1024   # 16-128 KB -> yellow ; > 128 KB -> red
# Cap for the cheap prefix read used to estimate character counts.
CONTEXT_READ_CAP = 1_048_576        # 1 MB


def get_context_color(size_bytes):
    """Return a colorama color for the given file/folder byte size."""
    if size_bytes > CONTEXT_MEDIUM_BYTES:
        return Fore.RED
    elif size_bytes > CONTEXT_LOW_BYTES:
        return Fore.YELLOW
    return Fore.GREEN


def format_tokens(tokens):
    """Format a token count as a compact human-readable string."""
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.2f}M tok"
    if tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K tok"
    return f"{tokens} tok"


def format_context(size_bytes, tokens):
    """Return 'SIZE / ~TOKENS' used across all file selectors."""
    return f"{format_size(size_bytes)} / ~{format_tokens(tokens)}"


def compute_file_tokens(files_info, cap_bytes=CONTEXT_READ_CAP):
    """Populate 'chars' and 'tokens' on each file info dict.

    Cheap (small) files are read fully up to the cap so the estimate is exact;
    huge files fall back to the on-disk byte size to avoid slow I/O.
    """
    ordered = sorted(files_info, key=lambda x: x.get('size', 0))
    for info in ordered:
        size = info.get('size', 0)
        full_path = info.get('full_path') or info.get('path')
        if size == 0 or not full_path:
            info['chars'] = 0
            info['tokens'] = 0
            continue
        words = 0
        if size <= cap_bytes:
            try:
                with open(full_path, 'rb') as fh:
                    raw = fh.read()
                chars = len(raw)
                # Cheap word count for a blended token estimate; decoding errors
                # are ignored so unusual encodings still yield a usable value.
                words = len(raw.decode('utf-8', errors='ignore').split())
            except OSError:
                chars = size
        else:
            chars = size
        info['chars'] = chars
        # Blended estimate: average of the char-based (chars / 4) and
        # word-based (words / 0.75) heuristics that approximate BPE
        # tokenizers. When the word count is unavailable (huge/skipped
        # files) fall back to the char-only approximation.
        if words > 0:
            info['tokens'] = max(int(0.5 * (chars / 4 + words / 0.75)), 1)
        else:
            info['tokens'] = max(chars // 4, 1)
    return files_info


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