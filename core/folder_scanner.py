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
    
    def get_structure(self, folder_path, indent=0, filter_folder=None, exclude_folders=None, exclude_extensions=None):
        """Get folder structure with size information."""
        if exclude_folders is None:
            exclude_folders = ['.git']
        if exclude_extensions is None:
            exclude_extensions = ['.svg', '.jpg', '.png', '.bin']

        structure = ""
        try:
            folder_path = validate_path(folder_path)
            items = os.listdir(folder_path)
        except Exception as e:
            logging.error(f"Could not list directory {folder_path}: {e}")
            return f"[ERROR] Could not list directory {folder_path}: {e}\n"

        for index, item in enumerate(items):
            if item in exclude_folders:
                continue

            item_path = os.path.join(folder_path, item)
            is_last = index == len(items) - 1

            if os.path.isdir(item_path):
                if filter_folder and filter_folder not in item:
                    continue

                size = get_folder_size(item_path)
                structure += '    ' * (indent // 4)
                structure += '└── ' if is_last else '├── '
                structure += f'[DIR] {item} ({format_size(size)})\n'

                structure += self.get_structure(item_path, indent + 4, filter_folder, exclude_folders, exclude_extensions)
            else:
                file_ext = os.path.splitext(item)[1].lower()
                if file_ext in exclude_extensions:
                    continue

                size = os.path.getsize(item_path)
                structure += '    ' * (indent // 4)
                structure += ('└── ' if is_last else '├── ') + f'[FILE] {item} ({format_size(size)})\n'

        return structure