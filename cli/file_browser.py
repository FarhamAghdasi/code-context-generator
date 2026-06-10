# cli/file_browser.py
"""Interactive file browser module with keyboard navigation."""

import os
import platform
from colorama import Fore, Style
from utils.helpers import getch, format_size, get_size_color


class FileBrowser:
    """Interactive file browser with selection capability."""
    
    def __init__(self, exclude_folders=None, exclude_extensions=None):
        """Initialize FileBrowser with exclusion rules."""
        self.exclude_folders = exclude_folders if exclude_folders is not None else ['.git']
        self.exclude_extensions = exclude_extensions if exclude_extensions is not None else ['.svg', '.jpg', '.png', '.bin']
    
    def browse(self, folder_path):
        """Interactive file browser with selection capability."""
        # Validate path
        if not os.path.exists(folder_path):
            print(f"{Fore.RED}Error: Path does not exist: {folder_path}{Style.RESET_ALL}")
            return None
        if not os.path.isdir(folder_path):
            print(f"{Fore.RED}Error: Path is not a directory: {folder_path}{Style.RESET_ALL}")
            return None
        
        folder_path = os.path.abspath(folder_path)
        
        # Build file tree
        file_tree = {}
        all_files = []
        
        for root, dirs, files in os.walk(folder_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.exclude_folders]
            
            rel_root = os.path.relpath(root, folder_path)
            if rel_root == '.':
                rel_root = '/'
            
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.exclude_extensions:
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, folder_path)
                try:
                    size = os.path.getsize(file_path)
                except:
                    size = 0
                
                all_files.append({
                    'path': rel_path,
                    'full_path': file_path,
                    'name': file,
                    'size': size,
                    'dir': rel_root
                })
        
        # Group by directory
        for file_info in all_files:
            dir_name = file_info['dir']
            if dir_name not in file_tree:
                file_tree[dir_name] = []
            file_tree[dir_name].append(file_info)
        
        if not file_tree:
            print(f"{Fore.YELLOW}No files found in the specified directory.{Style.RESET_ALL}")
            input("Press Enter to continue...")
            return []
        
        selected_files = set()
        current_dir = 0
        current_file = 0
        view_mode = 'dirs'  # 'dirs' or 'files'
        
        dirs = sorted(file_tree.keys())
        
        while True:
            # Clear screen
            os.system('cls' if platform.system() == 'Windows' else 'clear')
            
            print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Interactive File Browser - {folder_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Selected: {len(selected_files)} files{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Commands: ↑↓=Navigate | →=Enter Dir | ←=Back | SPACE=Select | A=Select All | "
                  f"N=Deselect All | ENTER=Done | Q=Quit{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
            
            if view_mode == 'dirs':
                print(f"{Fore.GREEN}Directories:{Style.RESET_ALL}\n")
                for idx, dir_name in enumerate(dirs):
                    file_count = len(file_tree[dir_name])
                    total_size = sum(f['size'] for f in file_tree[dir_name])
                    size_str = format_size(total_size)
                    size_color = get_size_color(total_size)
                    
                    prefix = "> " if idx == current_dir else "  "
                    selected_count = sum(1 for f in file_tree[dir_name] if f['path'] in selected_files)
                    status = f"[{selected_count}/{file_count}]" if selected_count > 0 else ""
                    
                    if idx == current_dir:
                        print(f"{Fore.GREEN}{prefix}📁 {dir_name} {status} ({file_count} files, {size_color}{size_str}{Style.RESET_ALL})")
                    else:
                        print(f"{prefix}📁 {dir_name} {status} ({file_count} files, {size_color}{size_str}{Style.RESET_ALL})")
            
            else:  # view_mode == 'files'
                current_dir_name = dirs[current_dir]
                files_in_dir = file_tree[current_dir_name]
                
                print(f"{Fore.GREEN}Files in: {current_dir_name}{Style.RESET_ALL}\n")
                for idx, file_info in enumerate(files_in_dir):
                    size_str = format_size(file_info['size'])
                    size_color = get_size_color(file_info['size'])
                    
                    prefix = "> " if idx == current_file else "  "
                    checkbox = "[X]" if file_info['path'] in selected_files else "[ ]"
                    
                    if idx == current_file:
                        print(f"{Fore.GREEN}{prefix}{checkbox} 📄 {file_info['name']} ({size_color}{size_str}{Style.RESET_ALL})")
                    elif file_info['path'] in selected_files:
                        print(f"{Fore.CYAN}{prefix}{checkbox} 📄 {file_info['name']} ({size_color}{size_str}{Style.RESET_ALL})")
                    else:
                        print(f"{prefix}{checkbox} 📄 {file_info['name']} ({size_color}{size_str}{Style.RESET_ALL})")
            
            # Get user input
            key = getch()
            
            # Handle key presses
            if key == 'UP':
                if view_mode == 'dirs':
                    current_dir = (current_dir - 1) % len(dirs)
                else:
                    current_file = (current_file - 1) % len(file_tree[dirs[current_dir]])
            elif key == 'DOWN':
                if view_mode == 'dirs':
                    current_dir = (current_dir + 1) % len(dirs)
                else:
                    current_file = (current_file + 1) % len(file_tree[dirs[current_dir]])
            elif key == 'RIGHT':
                if view_mode == 'dirs':
                    view_mode = 'files'
                    current_file = 0
            elif key == 'LEFT':
                if view_mode == 'files':
                    view_mode = 'dirs'
            elif key in ['\r', '\n']:  # Enter
                return list(selected_files)
            elif key == ' ':  # Space
                if view_mode == 'files':
                    current_dir_name = dirs[current_dir]
                    file_info = file_tree[current_dir_name][current_file]
                    if file_info['path'] in selected_files:
                        selected_files.remove(file_info['path'])
                    else:
                        selected_files.add(file_info['path'])
            elif key.lower() == 'a':  # Select all in current directory
                if view_mode == 'files':
                    current_dir_name = dirs[current_dir]
                    for file_info in file_tree[current_dir_name]:
                        selected_files.add(file_info['path'])
            elif key.lower() == 'n':  # Deselect all in current directory
                if view_mode == 'files':
                    current_dir_name = dirs[current_dir]
                    for file_info in file_tree[current_dir_name]:
                        selected_files.discard(file_info['path'])
            elif key.lower() == 'q' or key == '\x1b':  # Q or ESC
                return None