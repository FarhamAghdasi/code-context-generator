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


class OutputGenerator:
    """Handles output formatting, saving, and file operations."""
    
    def __init__(self):
        """Initialize OutputGenerator."""
        pass
    
    def format_output(self, structure, contents, output_format="txt", prompt_template=None):
        """Format output with optional prompt template."""
        final_output = ""
        
        # Add prompt template if selected
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
        else:  # txt
            output = f"Folder Structure:\n{structure}\n\nFile Contents:{contents}"
            return final_output + output
    
    def save_and_open(self, output, folder_path, output_format="txt", split_if_large=True, copy_to_clipboard=False):
        """Save output to file and optionally open it."""
        try:
            # Save to output directory in current path
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            extension = {"txt": "txt", "json": "json", "md": "md", "html": "html"}[output_format]
            max_size = 12000
            
            # Fix: Check if copy_to_clipboard is True and call the function correctly
            if copy_to_clipboard:
                clipboard_copy(output)
                
            if split_if_large and len(output) > max_size:
                print(f"{Fore.YELLOW}⚠️ Output exceeds {max_size:,} characters.{Style.RESET_ALL}")
                user_choice = input(f"Split into multiple files? (y/n): ").strip().lower()
                if user_choice == "y":
                    parts = [output[i:i+max_size] for i in range(0, len(output), max_size)]
                    saved_paths = []
                    for idx, part in enumerate(parts, start=1):
                        filename = f"project_structure_part{idx}.{extension}"
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(part)
                        saved_paths.append(filepath)
                    logging.info(f"Output saved in {len(saved_paths)} files")
                    return saved_paths
                    
            filename = f"project_structure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
                
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