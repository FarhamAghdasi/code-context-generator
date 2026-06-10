# core/file_processor.py
"""File processing module for reading and analyzing files."""

import os
import re
import logging
import chardet
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from colorama import Fore, Style


class FileProcessor:
    """Handles file reading, encoding detection, minification, and content filtering."""
    
    def __init__(self):
        """Initialize FileProcessor."""
        pass
    
    def is_binary_file(self, file_path):
        """Check if a file is binary."""
        try:
            with open(file_path, "rb") as f:
                content = f.read(1024)
                result = chardet.detect(content)
                return result["confidence"] < 0.9 or result["encoding"] is None
        except Exception:
            return True
    
    def check_sensitive_content(self, content):
        """Check for sensitive content like API keys."""
        sensitive_patterns = [
            r"API_KEY\s*=\s*['\"][A-Za-z0-9_-]+['\"]",
            r"SECRET_KEY\s*=\s*['\"][A-Za-z0-9_-]+['\"]",
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][A-Za-z0-9_-]+['\"]"
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logging.warning("Potential sensitive content detected in file")
                return True
        return False
    
    def minify_content(self, content, file_ext):
        """Minify file content to reduce size."""
        if not content:
            return content
        
        # Remove comments for various languages
        if file_ext in ['.py']:
            # Remove Python comments but keep docstrings
            lines = content.split('\n')
            minified_lines = []
            in_docstring = False
            for line in lines:
                stripped = line.strip()
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = not in_docstring
                    minified_lines.append(line)
                elif not in_docstring and stripped.startswith('#'):
                    continue
                elif stripped:
                    minified_lines.append(line)
            content = '\n'.join(minified_lines)
        
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx', '.java', '.cs', '.go', '.php']:
            # Remove single line comments
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            # Remove multi-line comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        elif file_ext in ['.html', '.xml']:
            # Remove HTML/XML comments
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        elif file_ext in ['.css', '.scss']:
            # Remove CSS comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content
    
    def read_file(self, file_path, keyword=None, regex=None, minify=False):
        """Read file content with encoding detection and optional minification."""
        if self.is_binary_file(file_path):
            logging.info(f"Skipping binary file: {file_path}")
            return None

        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result["encoding"] if result["encoding"] else "utf-8"
                content = raw_data.decode(encoding, errors="replace")
            
            if self.check_sensitive_content(content):
                print(f"{Fore.YELLOW}⚠ Warning: Sensitive content detected in {file_path}. Masking...{Style.RESET_ALL}")
                content = "[MASKED SENSITIVE CONTENT]"

            # Apply minification if enabled
            if minify and content != "[MASKED SENSITIVE CONTENT]":
                file_ext = os.path.splitext(file_path)[1].lower()
                content = self.minify_content(content, file_ext)

            if keyword and keyword.lower() not in content.lower():
                return None
            if regex and not re.search(regex, content, re.IGNORECASE):
                return None
            
            return f"\n{'-' * 40}\nFile: {file_path}\n{'-' * 40}\n{content}\n"
        except Exception as e:
            logging.error(f"Could not read {file_path}: {e}")
            return f"\n[ERROR] Could not read {file_path}: {e}\n"
    
    def get_file_contents(self, folder_path, filter_folder=None, exclude_folders=None, exclude_extensions=None, 
                         keyword=None, regex=None, min_size=0, modified_after=None, minify=False, 
                         selected_files=None):
        """Get file contents with optional file selection."""
        if exclude_folders is None:
            exclude_folders = ['.git']
        if exclude_extensions is None:
            exclude_extensions = ['.svg', '.jpg', '.png', '.bin']

        contents = ""
        file_list = []
        
        try:
            from utils.helpers import validate_path
            folder_path = validate_path(folder_path)
            
            for root, dirs, files in os.walk(folder_path):
                path_parts = os.path.normpath(root).split(os.sep)
                if any(part in exclude_folders for part in path_parts):
                    continue
                if filter_folder and filter_folder not in root:
                    continue
                
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in exclude_extensions:
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    # Check if file is in selected files (if selection is active)
                    if selected_files is not None:
                        rel_path = os.path.relpath(file_path, folder_path)
                        if rel_path not in selected_files:
                            continue
                    
                    if min_size > 0 and os.path.getsize(file_path) < min_size:
                        continue
                    
                    if modified_after:
                        import datetime
                        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime < modified_after:
                            continue
                    
                    file_list.append(file_path)
        except Exception as e:
            logging.error(f"Could not process directory {folder_path}: {e}")
            return f"[ERROR] Could not process directory {folder_path}: {e}\n"

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(tqdm(
                executor.map(lambda f: self.read_file(f, keyword, regex, minify), file_list),
                total=len(file_list),
                desc="Processing files",
                unit="file"
            ))
        
        return "".join([r for r in results if r])