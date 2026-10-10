# core/folder_scanner.py
"""Folder scanning module for project structure detection and tree generation."""

import os
import logging
from utils.helpers import get_folder_size, format_size, validate_path


class FolderScanner:
    """Handles folder scanning, project type detection, and structure generation."""
    
    def __init__(self, config_manager):
        """Initialize FolderScanner with config manager."""
        self.config_manager = config_manager
    
    def detect_project_type_advanced(self, folder_path):
        """Advanced project type detection based on files and structure."""
        try:
            folder_path = validate_path(folder_path)
            
            # Count files by extension
            file_counts = {}
            total_files = 0
            
            for root, dirs, files in os.walk(folder_path):
                # Skip common exclude folders
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.venv', 'vendor']]
                
                for file in files:
                    total_files += 1
                    ext = os.path.splitext(file)[1].lower()
                    file_counts[ext] = file_counts.get(ext, 0) + 1
            
            if total_files == 0:
                return "generic", 0
            
            # Check for specific project files first
            items = os.listdir(folder_path)
            
            # Python indicators
            python_files = [f for f in ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile", "poetry.lock"] if f in items]
            python_percentage = (file_counts.get('.py', 0) / total_files) * 100
            
            # Node.js indicators
            nodejs_files = [f for f in ["package.json", "npm-shrinkwrap.json", "yarn.lock", "package-lock.json"] if f in items]
            js_percentage = ((file_counts.get('.js', 0) + file_counts.get('.ts', 0) + file_counts.get('.jsx', 0) + file_counts.get('.tsx', 0)) / total_files) * 100
            
            # Java indicators
            java_files = [f for f in ["pom.xml", "build.gradle", "build.gradle.kts"] if f in items]
            java_percentage = (file_counts.get('.java', 0) / total_files) * 100
            
            # Go indicators
            go_files = [f for f in ["go.mod", "go.sum"] if f in items]
            go_percentage = (file_counts.get('.go', 0) / total_files) * 100
            
            # C# indicators
            csharp_files = [f for f in items if f.endswith('.csproj') or f.endswith('.sln')]
            csharp_percentage = (file_counts.get('.cs', 0) / total_files) * 100
            
            # PHP indicators
            php_files = [f for f in ["composer.json", "composer.lock"] if f in items]
            php_percentage = (file_counts.get('.php', 0) / total_files) * 100
            
            # Determine project type with confidence
            scores = {
                "python": (len(python_files) * 30 + python_percentage),
                "nodejs": (len(nodejs_files) * 30 + js_percentage),
                "java": (len(java_files) * 30 + java_percentage),
                "go": (len(go_files) * 30 + go_percentage),
                "csharp": (len(csharp_files) * 30 + csharp_percentage),
                "php": (len(php_files) * 30 + php_percentage)
            }
            
            if max(scores.values()) > 0:
                detected_type = max(scores, key=scores.get)
                confidence = min(scores[detected_type], 100)
                return detected_type, confidence
            
        except Exception as e:
            logging.error(f"Error detecting project type: {e}")
        
        return "generic", 0
    
    def get_structure(self, folder_path, indent=0, filter_folder=None, exclude_folders=None, exclude_extensions=None,
                      selected_files=None, base_path=None):
        """Get folder structure with size information.

        When selected_files is provided (a list of paths relative to base_path),
        only files in that set - and the directories containing them - are rendered.
        """
        if exclude_folders is None:
            exclude_folders = ['.git']
        if exclude_extensions is None:
            exclude_extensions = ['.svg', '.jpg', '.png', '.bin']

        if base_path is None:
            base_path = folder_path

        structure = ""
        try:
            folder_path = validate_path(folder_path)
            items = os.listdir(folder_path)
        except Exception as e:
            logging.error(f"Could not list directory {folder_path}: {e}")
            return f"[ERROR] Could not list directory {folder_path}: {e}\n"

        # Build the list of visible items first so that is_last is computed correctly
        filtered_items = []
        for item in items:
            if item in exclude_folders:
                continue
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                if filter_folder and filter_folder not in item:
                    continue
                if selected_files is not None:
                    # Keep the directory only if it (or a descendant) contains a selected file
                    rel_dir = os.path.relpath(item_path, base_path)
                    prefix = rel_dir + os.sep
                    has_match = any(sf == rel_dir or sf.startswith(prefix) for sf in selected_files)
                    if not has_match:
                        continue
                filtered_items.append((item, item_path, True))
            else:
                file_ext = os.path.splitext(item)[1].lower()
                if file_ext in exclude_extensions:
                    continue
                if selected_files is not None:
                    rel_path = os.path.relpath(item_path, base_path)
                    if rel_path not in selected_files:
                        continue
                filtered_items.append((item, item_path, False))

        for index, (item, item_path, is_dir) in enumerate(filtered_items):
            is_last = index == len(filtered_items) - 1
            if is_dir:
                size = get_folder_size(item_path)
                structure += '    ' * (indent // 4)
                structure += '└── ' if is_last else '├── '
                structure += f'[DIR] {item} ({format_size(size)})\n'
                structure += self.get_structure(
                    item_path, indent + 4, filter_folder,
                    exclude_folders, exclude_extensions,
                    selected_files=selected_files, base_path=base_path
                )
            else:
                size = os.path.getsize(item_path)
                structure += '    ' * (indent // 4)
                structure += ('└── ' if is_last else '├── ') + f'[FILE] {item} ({format_size(size)})\n'
        return structure