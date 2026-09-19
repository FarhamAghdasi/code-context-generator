# cli/interactive_mode.py
"""Interactive mode module with menu-driven interface."""

import os
import datetime
from colorama import Fore, Style
from utils.helpers import select_from_list, validate_path
from utils.git_utils import clone_remote_repo
from core.config_manager import ConfigManager
from core.folder_scanner import FolderScanner
from prompts.templates import PROMPT_TEMPLATES
from cli.file_browser import FileBrowser, TreeFileBrowser


class InteractiveMode:
    """Interactive mode handler with step-by-step user input."""
    
    def __init__(self):
        """Initialize InteractiveMode."""
        self.config_manager = ConfigManager()
        self.folder_scanner = FolderScanner(self.config_manager)
    
    def select_prompts(self):
        """Select prompt templates interactively."""
        prompts = list(PROMPT_TEMPLATES.keys())
        prompt_names = [f"{PROMPT_TEMPLATES[k]['name']}" for k in prompts]
        
        print(f"\n{Fore.CYAN}Select Prompt Templates (you can select multiple):{Style.RESET_ALL}\n")
        for idx, name in enumerate(prompt_names):
            print(f"  {idx + 1}. {name}")
        print(f"  0. No prompt template")
        
        selected_indices = input(f"\n{Fore.YELLOW}Enter numbers separated by commas (e.g., 1,3): {Style.RESET_ALL}").strip()
        
        if not selected_indices or selected_indices == "0":
            return []
        
        try:
            indices = [int(x.strip()) - 1 for x in selected_indices.split(',') if x.strip()]
            selected = []
            for idx in indices:
                if 0 <= idx < len(prompts):
                    selected.append(prompts[idx])
            return selected
        except:
            return []
    
    def run(self):
        """Run interactive mode with menu selection."""
        
        # Step 1: Choose mode
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Welcome to Enhanced Project Structure Reader{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
        
        modes = [
            "Standard Mode (with prompts and filters)",
            "Interactive File Browser (select specific files)",
            "Tree View Picker (navigate folders and select files)"
        ]
        
        mode_choice = select_from_list(modes, "Select Mode:")
        if mode_choice is None:
            return None
        
        # Step 2: Project type selection
        project_types = self.config_manager.get_all_project_types()
        suggested_type, confidence = self.folder_scanner.detect_project_type_advanced(os.getcwd())
        
        type_options = []
        for pt in project_types:
            color = self.config_manager.get_project_color(pt)
            if pt == suggested_type:
                type_options.append(f"{color}{pt} (Detected: {confidence:.0f}% confidence){Style.RESET_ALL}")
            else:
                type_options.append(f"{color}{pt}{Style.RESET_ALL}")
        
        project_type_display = select_from_list(type_options, "Select Project Type:")
        if project_type_display is None:
            return None
        
        project_type = project_types[type_options.index(project_type_display)]
        config = self.config_manager.get_project_config(project_type)
        
        # Step 3: Folder path
        print(f"\n{Fore.CYAN}Enter folder path or GitHub URL{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Default: {os.getcwd()}{Style.RESET_ALL}")
        folder_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
        
        if not folder_input:
            folder_path = os.getcwd()
        elif folder_input.startswith("http"):
            try:
                folder_path = clone_remote_repo(folder_input)
                print(f"{Fore.GREEN}Repository cloned successfully to: {folder_path}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error cloning repository: {e}{Style.RESET_ALL}")
                return None
        else:
            try:
                folder_path = validate_path(folder_input)
            except ValueError as e:
                print(f"{Fore.RED}{e}{Style.RESET_ALL}")
                return None
        
        # Step 4: File browser mode or standard mode
        selected_files = None
        if mode_choice == modes[1]:
            file_browser = FileBrowser(config['exclude_folders'], config['exclude_extensions'])
            selected_files = file_browser.browse(folder_path)
            if selected_files is None:
                print(f"{Fore.RED}File selection cancelled.{Style.RESET_ALL}")
                return None
            print(f"\n{Fore.GREEN}Selected {len(selected_files)} files.{Style.RESET_ALL}")
            
            filter_folder = None
            keyword = None
            regex = None
            min_size = 0
            modified_after = None
        elif mode_choice == modes[2]:
            tree_browser = TreeFileBrowser(config['exclude_folders'], config['exclude_extensions'])
            selected_files = tree_browser.browse(folder_path)
            if selected_files is None:
                print(f"{Fore.RED}File selection cancelled.{Style.RESET_ALL}")
                return None
            print(f"\n{Fore.GREEN}Selected {len(selected_files)} files.{Style.RESET_ALL}")
            
            filter_folder = None
            keyword = None
            regex = None
            min_size = 0
            modified_after = None
        else:
            # Standard mode - additional filters
            filters = [
                "Filter by folder name",
                "Filter by keyword",
                "Filter by regex",
                "Filter by minimum size",
                "Filter by modification date",
                "No additional filters"
            ]
            
            filter_choice = select_from_list(filters, "Select Filter Options:", multi_select=True)
            
            filter_folder = None
            keyword = None
            regex = None
            min_size = 0
            modified_after = None
            
            if filter_choice and "Filter by folder name" in filter_choice:
                filter_folder = input(f"\n{Fore.YELLOW}Enter folder name to filter: {Style.RESET_ALL}").strip() or None
            
            if filter_choice and "Filter by keyword" in filter_choice:
                keyword = input(f"\n{Fore.YELLOW}Enter keyword to filter: {Style.RESET_ALL}").strip() or None
            
            if filter_choice and "Filter by regex" in filter_choice:
                regex = input(f"\n{Fore.YELLOW}Enter regex pattern: {Style.RESET_ALL}").strip() or None
            
            if filter_choice and "Filter by minimum size" in filter_choice:
                size_input = input(f"\n{Fore.YELLOW}Enter minimum file size in bytes: {Style.RESET_ALL}").strip()
                min_size = int(size_input) if size_input.isdigit() else 0
            
            if filter_choice and "Filter by modification date" in filter_choice:
                date_input = input(f"\n{Fore.YELLOW}Enter date (YYYY-MM-DD): {Style.RESET_ALL}").strip()
                try:
                    modified_after = datetime.datetime.strptime(date_input, "%Y-%m-%d")
                except:
                    modified_after = None
        
        # Step 5: Prompt template selection
        selected_prompt_keys = self.select_prompts()
        
        # Build combined prompt
        combined_prompt = ""
        if selected_prompt_keys:
            for key in selected_prompt_keys:
                combined_prompt += PROMPT_TEMPLATES[key]['template'] + "\n\n"
        
        # Step 6: Output format
        formats = ["txt", "json", "md", "html"]
        format_options = [f.upper() for f in formats]
        format_choice = select_from_list(format_options, "Select Output Format:")
        if format_choice is None:
            return None
        output_format = formats[format_options.index(format_choice)]
        
        # Step 7: Minify option
        minify_options = ["Yes - Minify content (reduce size)", "No - Keep original content"]
        minify_choice = select_from_list(minify_options, "Enable Minification?")
        minify = (minify_choice == minify_options[0])
        
        # Step 8: Copy to clipboard
        clipboard_options = ["Yes - Copy to clipboard", "No"]
        clipboard_choice = select_from_list(clipboard_options, "Copy to Clipboard?")
        copy_to_clipboard = (clipboard_choice == clipboard_options[0])
        
        return {
            'folder_path': folder_path,
            'project_type': project_type,
            'filter_folder': filter_folder,
            'exclude_folders': config['exclude_folders'],
            'exclude_extensions': config['exclude_extensions'],
            'keyword': keyword,
            'regex': regex,
            'output_format': output_format,
            'min_size': min_size,
            'modified_after': modified_after,
            'minify': minify,
            'copy_to_clipboard': copy_to_clipboard,
            'prompt_template': combined_prompt if combined_prompt else None,
            'selected_files': selected_files
        }