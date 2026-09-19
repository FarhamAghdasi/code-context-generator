# core/output_generator.py
"""Output generation module for formatting and saving results."""

import os
import json
import datetime
import platform
import logging
import markdown2
from colorama import Fore, Style
from utils.clipboard import copy_to_clipboard as clipboard_copy
from core.smart_splitter import SmartSplitter
from core.config_manager import ConfigManager


class OutputGenerator:
    """Handles output formatting, saving, and file operations."""
    
    def __init__(self, config_manager=None):
        """Initialize OutputGenerator."""
        self.smart_splitter = SmartSplitter()
        self.config_manager = config_manager or ConfigManager()
        self.user_split_preference = None
        self._load_split_preference()
    
    def _load_split_preference(self):
        """Load user's split preference from settings."""
        settings = self.config_manager.load_settings()
        if settings:
            self.user_split_preference = settings.get('split_preference')
            logging.info(f"Loaded split preference: {self.user_split_preference}")
    
    def _save_split_preference(self, preference, folder_path=None, profile_name=None):
        """Save user's split preference to settings."""
        try:
            settings = self.config_manager.load_settings(profile_name=profile_name, folder_path=folder_path) or {}
            settings['split_preference'] = preference
            if profile_name:
                self.config_manager.save_settings(profile_name, settings, scope="system")
            elif folder_path:
                self.config_manager.save_settings("default", settings, scope="dir", folder_path=folder_path)
            self.user_split_preference = preference
            logging.info(f"Saved split preference: {preference}")
        except Exception as e:
            logging.warning(f"Could not save split preference: {e}")
    
    def format_output(self, structure, contents, output_format="txt", prompt_template=None):
        """Format output with optional prompt template."""
        final_output = ""
        
        if prompt_template:
            final_output += prompt_template + "\n\n"
        
        if output_format == "json":
            output_dict = {
                "prompt": prompt_template if prompt_template else "",
                "folder_structure": structure,
                "file_contents": contents
            }
            return json.dumps(output_dict, indent=2, ensure_ascii=False)
        elif output_format == "md":
            output = f"# Project Structure\n\n```tree\n{structure}\n```\n\n# File Contents\n\n```text\n{contents}\n```"
            return final_output + output
        elif output_format == "html":
            md_content = f"# Project Structure\n\n```tree\n{structure}\n```\n\n# File Contents\n\n```text\n{contents}\n```"
            return final_output + markdown2.markdown(md_content)
        else:
            output = f"Folder Structure:\n{structure}\n\nFile Contents:{contents}"
            return final_output + output
    
    def save_and_open(self, output, folder_path, output_format="txt", split_if_large=True, copy_to_clipboard=False):
        """Original save method for backward compatibility."""
        return self.save_with_smart_split(output, folder_path, output_format, copy_to_clipboard, interactive_split=split_if_large)
    
    def save_with_smart_split(self, output, folder_path, output_format="txt", copy_to_clipboard=False, interactive_split=True):
        """Save output with advanced splitting options."""
        try:
            output_size = len(output)
            extension = {"txt": "txt", "json": "json", "md": "md", "html": "html"}[output_format]
            
            # Copy to clipboard if requested
            if copy_to_clipboard:
                clipboard_copy(output)
                print(f"{Fore.GREEN}Copied to clipboard{Style.RESET_ALL}")
            
            # Check if splitting is needed
            should_split = False
            use_advanced = False
            
            if interactive_split and output_size > 12000:  # 12KB threshold
                print(f"\n{Fore.YELLOW}Output size: {output_size:,} characters{Style.RESET_ALL}")
                
                # Check if user has saved preference
                if self.user_split_preference == 'simple':
                    print(f"{Fore.CYAN}Using simple split mode (your saved preference){Style.RESET_ALL}")
                    should_split = True
                    use_advanced = False
                elif self.user_split_preference == 'advanced':
                    print(f"{Fore.CYAN}Using advanced split mode (your saved preference){Style.RESET_ALL}")
                    should_split = True
                    use_advanced = True
                else:
                    # Ask user what they want to do
                    print(f"\n{Fore.CYAN}How would you like to split the output?{Style.RESET_ALL}")
                    print(f"  {Fore.GREEN}1.{Style.RESET_ALL} Simple split (quick & easy)")
                    print(f"  {Fore.GREEN}2.{Style.RESET_ALL} Advanced split (custom strategy, boundaries, etc.)")
                    print(f"  {Fore.GREEN}3.{Style.RESET_ALL} Don't split (save as single file)")
                    print(f"  {Fore.GREEN}4.{Style.RESET_ALL} Remember my choice for future (don't ask again)")
                    
                    choice = input(f"\n{Fore.YELLOW}Enter your choice (1-4): {Style.RESET_ALL}").strip()
                    
                    if choice == '1':
                        should_split = True
                        use_advanced = False
                        self.user_split_preference = 'simple'
                    elif choice == '2':
                        should_split = True
                        use_advanced = True
                        self.user_split_preference = 'advanced'
                    elif choice == '3':
                        should_split = False
                        self.user_split_preference = 'no_split'
                    elif choice == '4':
                        # Show options again to set preference
                        print(f"\n{Fore.CYAN}Set your default preference:{Style.RESET_ALL}")
                        print(f"  {Fore.GREEN}1.{Style.RESET_ALL} Always use Simple split")
                        print(f"  {Fore.GREEN}2.{Style.RESET_ALL} Always use Advanced split")
                        print(f"  {Fore.GREEN}3.{Style.RESET_ALL} Never split (single file)")
                        
                        pref_choice = input(f"\n{Fore.YELLOW}Enter your choice (1-3): {Style.RESET_ALL}").strip()
                        if pref_choice == '1':
                            self.user_split_preference = 'simple'
                            should_split = True
                            use_advanced = False
                        elif pref_choice == '2':
                            self.user_split_preference = 'advanced'
                            should_split = True
                            use_advanced = True
                        elif pref_choice == '3':
                            self.user_split_preference = 'no_split'
                            should_split = False
                    else:
                        # Default to simple split
                        should_split = True
                        use_advanced = False
            
            # Handle splitting
            if should_split:
                if use_advanced:
                    # Get splitting preferences from user
                    preferences = self.smart_splitter.get_split_preferences_interactive()
                    
                    # Split the content
                    print(f"\n{Fore.CYAN}Splitting content...{Style.RESET_ALL}")
                    chunks = self.smart_splitter.split_content(output, preferences)
                    
                    # Validate split
                    stats = self.smart_splitter.validate_split(chunks)
                    
                    print(f"\n{Fore.GREEN}Split Results:{Style.RESET_ALL}")
                    print(f"  Number of files: {stats['num_chunks']}")
                    print(f"  Average size: {stats['avg_size']:,} chars")
                    print(f"  Size range: {stats['min_size']:,} - {stats['max_size']:,} chars")
                    print(f"  Balanced: {'Yes' if stats['is_balanced'] else 'No'}")
                    
                    # Save split files
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_dir = os.path.join("output", f"split_{timestamp}")
                    
                    print(f"\n{Fore.CYAN}Saving split files...{Style.RESET_ALL}")
                    saved_paths = self.smart_splitter.save_split_files(
                        chunks, output_dir,
                        base_name=f"project_structure_{timestamp}",
                        extension=extension
                    )
                    
                    print(f"\n{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}SUCCESS! Split into {len(saved_paths)} files{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}Location: {output_dir}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
                    
                    return saved_paths
                else:
                    # Simple split (original behavior)
                    max_size = 12000
                    chunks = []
                    for i in range(0, len(output), max_size):
                        chunks.append(output[i:i+max_size])
                    
                    output_dir = "output"
                    os.makedirs(output_dir, exist_ok=True)
                    
                    saved_paths = []
                    for idx, chunk in enumerate(chunks, start=1):
                        filename = f"project_structure_part{idx}.{extension}"
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(chunk)
                        saved_paths.append(filepath)
                    
                    print(f"\n{Fore.GREEN}Saved in {len(saved_paths)} files{Style.RESET_ALL}")
                    return saved_paths
            
            # If not splitting, save as single file
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"project_structure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
            
            print(f"\n{Fore.GREEN}Saved to: {filepath}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}File size: {len(output.encode('utf-8')):,} bytes{Style.RESET_ALL}")
            
            # Try to open the file
            try:
                if platform.system() == 'Windows':
                    os.startfile(filepath)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{filepath}"')
                else:
                    os.system(f'xdg-open "{filepath}"')
            except Exception as e:
                logging.warning(f"Could not open file {filepath}: {e}")
            
            return filepath
            
        except Exception as e:
            logging.error(f"Error saving output: {e}")
            raise ValueError(f"Error saving output: {e}")