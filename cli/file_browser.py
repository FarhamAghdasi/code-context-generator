# cli/file_browser.py
"""Interactive file browser module with keyboard navigation."""

import os
import platform
from dataclasses import dataclass, field
from typing import List, Optional
from colorama import Fore, Style
from utils.helpers import getch, format_size, get_size_color


@dataclass
class TreeNode:
    """Tree node for folder/file structure."""
    name: str
    path: str
    is_dir: bool
    children: List["TreeNode"] = field(default_factory=list)
    expanded: bool = False
    selected: bool = False


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


class TreeFileBrowser:
    """Interactive tree view file browser with expand/collapse and selection."""

    def __init__(self, exclude_folders=None, exclude_extensions=None):
        self.exclude_folders = set(exclude_folders) if exclude_folders else {'.git'}
        self.exclude_extensions = set(exclude_extensions) if exclude_extensions else {'.svg', '.jpg', '.png', '.bin'}

    def _build_tree(self, folder_path, rel_prefix=""):
        nodes = []
        try:
            entries = sorted(os.listdir(folder_path), key=lambda s: s.lower())
        except OSError:
            return nodes

        for entry in entries:
            if entry in self.exclude_folders:
                continue
            full_path = os.path.join(folder_path, entry)
            if os.path.islink(full_path):
                continue
            rel_path = os.path.join(rel_prefix, entry) if rel_prefix else entry
            if os.path.isdir(full_path):
                children = self._build_tree(full_path, rel_path)
                nodes.append(TreeNode(name=entry, path=rel_path, is_dir=True, children=children))
            elif os.path.isfile(full_path):
                ext = os.path.splitext(entry)[1].lower()
                if ext in self.exclude_extensions:
                    continue
                nodes.append(TreeNode(name=entry, path=rel_path, is_dir=False))
        return nodes

    def _get_visible_nodes(self, root):
        visible = []

        def walk(nodes, prefix):
            for idx, node in enumerate(nodes):
                visible.append((node, prefix))
                if node.is_dir and node.expanded and node.children:
                    extension = "│   " if idx < len(nodes) - 1 else "    "
                    walk(node.children, prefix + extension)

        walk([root], "")
        return visible

    def _render(self, root, current_node, selected_files):
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        visible = self._get_visible_nodes(root)
        selected_count = self._count_selected_files(root)
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Tree View - {self.folder_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Selected: {selected_count} files{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Commands: ↑↓=Navigate | →=Expand | ←=Collapse | SPACE=Select | A=All | N=None | ENTER=Done | Q=Quit{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

        for node, prefix in visible:
            if node.is_dir:
                marker = "[-]" if node.expanded else "[+]"
            else:
                marker = "[X]" if node.path in selected_files else "[ ]"
            cursor = "> " if node is current_node else "  "
            size_info = ""
            if not node.is_dir and node.path in selected_files:
                try:
                    size = os.path.getsize(os.path.join(self.folder_path, node.path))
                    size_info = f" ({format_size(size)})"
                except OSError:
                    size_info = ""
            line = f"{prefix}{marker} {node.name}{size_info}"
            if node is current_node:
                print(f"{Fore.GREEN}{cursor}{line}{Style.RESET_ALL}")
            elif node.path in selected_files:
                print(f"{Fore.CYAN}{cursor}{line}{Style.RESET_ALL}")
            else:
                print(f"{cursor}{line}")

    def _count_selected_files(self, root):
        count = 0
        for node in self._flatten(root):
            if not node.is_dir and node.path in self._selected_files:
                count += 1
        return count

    def _flatten(self, root):
        result = []

        def walk(nodes):
            for node in nodes:
                result.append(node)
                if node.children:
                    walk(node.children)
        walk([root])
        return result

    def browse(self, folder_path):
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            print(f"{Fore.RED}Error: Path does not exist or is not a directory: {folder_path}{Style.RESET_ALL}")
            return None

        self.folder_path = os.path.abspath(folder_path)
        root = TreeNode(name=os.path.basename(self.folder_path) or self.folder_path, path="", is_dir=True, expanded=True)
        root.children = self._build_tree(self.folder_path)
        if not root.children:
            print(f"{Fore.YELLOW}No files found in the specified directory.{Style.RESET_ALL}")
            input("Press Enter to continue...")
            return []

        self._selected_files = set()
        current_node = root.children[0] if root.children else root
        visible_nodes = self._get_visible_nodes(root)

        while True:
            visible_nodes = self._get_visible_nodes(root)
            self._render(root, current_node, self._selected_files)
            key = getch()

            if key == 'UP':
                idx = next((i for i, (n, _) in enumerate(visible_nodes) if n is current_node), -1)
                if idx > 0:
                    current_node = visible_nodes[idx - 1][0]
            elif key == 'DOWN':
                idx = next((i for i, (n, _) in enumerate(visible_nodes) if n is current_node), -1)
                if idx < len(visible_nodes) - 1:
                    current_node = visible_nodes[idx + 1][0]
            elif key == 'RIGHT':
                if current_node.is_dir and not current_node.expanded:
                    current_node.expanded = True
                elif current_node.is_dir and current_node.children:
                    idx = next((i for i, (n, _) in enumerate(visible_nodes) if n is current_node), -1)
                    if idx + 1 < len(visible_nodes):
                        current_node = visible_nodes[idx + 1][0]
            elif key == 'LEFT':
                if current_node.is_dir and current_node.expanded:
                    current_node.expanded = False
                else:
                    parent = self._find_parent(root, current_node)
                    if parent is not None and parent is not root:
                        current_node = parent
            elif key == ' ':
                if current_node.is_dir:
                    self._toggle_folder(current_node)
                else:
                    if current_node.path in self._selected_files:
                        self._selected_files.discard(current_node.path)
                    else:
                        self._selected_files.add(current_node.path)
            elif key.lower() == 'a':
                for node in self._flatten(root):
                    if not node.is_dir:
                        self._selected_files.add(node.path)
            elif key.lower() == 'n':
                self._selected_files.clear()
            elif key in ['\r', '\n']:
                return list(self._selected_files)
            elif key.lower() == 'q' or key == '\x1b':
                return None

    def _toggle_folder(self, folder_node):
        selected = folder_node.path in self._selected_files
        if selected:
            self._deselect_folder(folder_node)
            self._selected_files.discard(folder_node.path)
        else:
            self._select_folder(folder_node)
            if folder_node.path:
                self._selected_files.add(folder_node.path)

    def _select_folder(self, node):
        if not node.is_dir:
            self._selected_files.add(node.path)
        else:
            for child in node.children:
                self._select_folder(child)

    def _deselect_folder(self, node):
        if not node.is_dir:
            self._selected_files.discard(node.path)
        else:
            for child in node.children:
                self._deselect_folder(child)

    def _find_parent(self, root, target):
        for child in root.children:
            result = self._find_parent_in_subtree(child, target)
            if result is not None:
                return result
        return None

    def _find_parent_in_subtree(self, node, target):
        for child in node.children:
            if child is target:
                return node
            result = self._find_parent_in_subtree(child, target)
            if result is not None:
                return result
        return None