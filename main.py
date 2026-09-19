# main.py
"""Enhanced project structure and file reader - Main entry point."""

import os
import sys
import datetime
import shutil
import gettext
from colorama import init, Fore, Style

# Initialize i18n
lang = os.getenv("LANG", "en")
try:
    if lang.startswith("fa"):
        translation = gettext.translation("messages", localedir="locale", languages=["fa"])
        translation.install()
        _ = translation.gettext
    else:
        _ = lambda x: x
except FileNotFoundError:
    _ = lambda x: x

# Import core modules
from core.config_manager import ConfigManager
from core.folder_scanner import FolderScanner
from core.file_processor import FileProcessor
from core.output_generator import OutputGenerator

# Import CLI modules
from cli.argument_parser import ArgumentParser
from cli.interactive_mode import InteractiveMode

# Import utilities
from utils.logger import setup_logging
from utils.git_utils import clone_remote_repo
from utils.helpers import format_size, validate_path
from utils.clipboard import copy_to_clipboard
from prompts.templates import PROMPT_TEMPLATES


def run_cli_mode(args):
    """Run in CLI (non-interactive) mode."""
    folder_path = None
    
    # Clone remote repository if specified
    if args.remote:
        folder_path = clone_remote_repo(args.remote)
    
    # Use custom path if provided
    if args.custom:
        folder_path = validate_path(args.custom[0])
    
    # If no path specified, use current directory
    if not folder_path:
        folder_path = os.getcwd()
    
    # Load configuration
    config_manager = ConfigManager()
    
    # Detect project type if not specified
    if args.project_type:
        project_type = args.project_type
    else:
        scanner = FolderScanner(config_manager)
        project_type, confidence = scanner.detect_project_type_advanced(folder_path)
        if confidence > 0:
            print(f"{Fore.CYAN}Detected project type: {project_type} ({confidence:.0f}% confidence){Style.RESET_ALL}")
    
    config = config_manager.get_project_config(project_type)
    
    # Override with custom values
    if args.custom:
        exclude_folders = [f.strip() for f in args.custom[1].split(',')]
        exclude_extensions = [e.strip().lower() for e in args.custom[2].split(',')]
    else:
        exclude_folders = config['exclude_folders']
        exclude_extensions = config['exclude_extensions']
    
    filter_folder = args.filter
    keyword = args.keyword
    regex = args.regex
    output_format = args.format if args.format else config['output_format']
    min_size = args.min_size
    
    # Parse modified_after date
    modified_after = None
    if args.modified_after:
        try:
            modified_after = datetime.datetime.strptime(args.modified_after, "%Y-%m-%d")
        except ValueError as e:
            print(f"{Fore.YELLOW}Warning: Invalid date format. Using YYYY-MM-DD. Error: {e}{Style.RESET_ALL}")
    
    minify = args.minify
    
    # Build prompt template
    prompt_template = ""
    if args.prompt:
        for prompt_key in args.prompt:
            if prompt_key in PROMPT_TEMPLATES:
                prompt_template += PROMPT_TEMPLATES[prompt_key]['template'] + "\n\n"
        print(f"{Fore.GREEN}Added {len(args.prompt)} prompt template(s){Style.RESET_ALL}")
    
    # Get folder structure and file contents
    print(f"{Fore.CYAN}Scanning folder structure...{Style.RESET_ALL}")
    scanner = FolderScanner(config_manager)
    structure = scanner.get_structure(
        folder_path,
        filter_folder=filter_folder,
        exclude_folders=exclude_folders,
        exclude_extensions=exclude_extensions
    )
    
    print(f"{Fore.CYAN}Processing file contents...{Style.RESET_ALL}")
    file_processor = FileProcessor()
    contents = file_processor.get_file_contents(
        folder_path,
        filter_folder=filter_folder,
        exclude_folders=exclude_folders,
        exclude_extensions=exclude_extensions,
        keyword=keyword,
        regex=regex,
        min_size=min_size,
        modified_after=modified_after,
        minify=minify
    )
    
    # Generate and save output
    print(f"{Fore.CYAN}Generating output...{Style.RESET_ALL}")
    output_generator = OutputGenerator()
    output = output_generator.format_output(structure, contents, output_format, prompt_template)
    
    # Use smart splitter for saving
    saved_path = output_generator.save_with_smart_split(
        output, 
        folder_path, 
        output_format, 
        copy_to_clipboard=args.copy,
        interactive_split=True
    )
    
    print(f"\n{Fore.GREEN}Output saved successfully{Style.RESET_ALL}")
    if isinstance(saved_path, list):
        print(f"{Fore.GREEN}Saved in {len(saved_path)} files{Style.RESET_ALL}")
        for path in saved_path:
            print(f"  Folder: {path}")
    else:
        print(f"{Fore.GREEN}Output saved to: {Fore.BLUE}{saved_path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Total size: {format_size(len(output.encode('utf-8')))}{Style.RESET_ALL}")
    
    # Clean up temporary directory if remote repo was cloned
    if args.remote and folder_path and folder_path == "temp_repo":
        shutil.rmtree(folder_path)
        print(f"{Fore.CYAN}Cleaned up temporary repository{Style.RESET_ALL}")


def run_interactive_mode(args):
    """Run in interactive mode."""
    interactive = InteractiveMode()
    result = interactive.run()
    
    if result is None:
        print(f"\n{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{_('Processing project')}...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    
    # Get folder structure
    scanner = FolderScanner(interactive.config_manager)
    structure = scanner.get_structure(
        result['folder_path'],
        filter_folder=result['filter_folder'],
        exclude_folders=result['exclude_folders'],
        exclude_extensions=result['exclude_extensions']
    )
    
    # Get file contents
    file_processor = FileProcessor()
    contents = file_processor.get_file_contents(
        result['folder_path'],
        filter_folder=result['filter_folder'],
        exclude_folders=result['exclude_folders'],
        exclude_extensions=result['exclude_extensions'],
        keyword=result['keyword'],
        regex=result['regex'],
        min_size=result['min_size'],
        modified_after=result['modified_after'],
        minify=result['minify'],
        selected_files=result.get('selected_files')
    )
    
    # Generate and save output
    output_generator = OutputGenerator()
    output = output_generator.format_output(
        structure, contents, result['output_format'], result['prompt_template']
    )
    
    # Use smart splitter for saving
    saved_path = output_generator.save_with_smart_split(
        output,
        result['folder_path'],
        result['output_format'],
        copy_to_clipboard=result['copy_to_clipboard'],
        interactive_split=True
    )
    
    print(f"\n{Fore.GREEN}Output saved successfully{Style.RESET_ALL}")
    if isinstance(saved_path, list):
        print(f"{Fore.GREEN}Saved in {len(saved_path)} files{Style.RESET_ALL}")
        for path in saved_path:
            print(f"  Folder: {path}")
    else:
        print(f"{Fore.GREEN}Output saved to: {Fore.BLUE}{saved_path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Total size: {format_size(len(output.encode('utf-8')))}{Style.RESET_ALL}")


def main():
    """Main entry point for the application."""
    init()  # Initialize colorama
    
    # Parse command line arguments
    arg_parser = ArgumentParser()
    args = arg_parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_file)
    
    try:
        # Check if we should run in CLI mode (non-interactive)
        if args.custom or args.remote or args.filter or args.keyword or args.regex or args.format:
            run_cli_mode(args)
        else:
            # Interactive mode
            run_interactive_mode(args)
            
    except ValueError as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        import logging
        logging.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()