# cli/interactive_mode.py
"""Interactive mode module with menu-driven interface."""

import os
import datetime
from colorama import Fore, Style
from utils.helpers import (
    select_from_list, validate_path, get_context_color,
    format_size, format_tokens, compute_file_tokens,
)
from utils.git_utils import clone_remote_repo
from core.config_manager import ConfigManager
from core.folder_scanner import FolderScanner
from prompts.templates import PROMPT_TEMPLATES
from cli.file_browser import FileBrowser, TreeFileBrowser
from cli.drag_drop import DragDropSelector

class InteractiveMode:
    """Interactive mode handler with step-by-step user input."""
    
    def __init__(self):
        """Initialize InteractiveMode."""
        self.config_manager = ConfigManager()
        self.folder_scanner = FolderScanner(self.config_manager)
    
    def select_prompts(self, saved_settings=None):
        """Select prompt templates interactively."""
        prompts = list(PROMPT_TEMPLATES.keys())
        prompt_names = [f"{PROMPT_TEMPLATES[k]['name']}" for k in prompts]
        
        saved_prompts = []
        if saved_settings:
            saved_prompts = saved_settings.get('prompt_keys', []) or []
        
        print(f"\n{Fore.CYAN}Select Prompt Templates (you can select multiple):{Style.RESET_ALL}\n")
        for idx, name in enumerate(prompt_names):
            marker = " (saved)" if prompts[idx] in saved_prompts else ""
            print(f"  {idx + 1}. {name}{marker}")
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

        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Welcome to Enhanced Project Structure Reader{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

        # Step 0: Load saved settings FIRST so the profile can pre-fill the
        # rest of the flow (project root and file selection).
        saved_settings = None
        load_choice = select_from_list(["Yes - Load saved settings", "No - Start fresh"], "Load saved settings?")
        if load_choice is None:
            return None
        if load_choice.startswith("Yes"):
            scope_choice = select_from_list(["System profile", "Directory config"], "Settings scope:")
            if scope_choice:
                if scope_choice.startswith("System"):
                    profile_names = self.config_manager.list_profiles()
                    if profile_names:
                        profile_choice = select_from_list(profile_names, "Select profile:")
                        if profile_choice:
                            saved_settings = self.config_manager.load_settings(profile_name=profile_choice, scope="system")
                    else:
                        print(f"{Fore.YELLOW}No system profiles found.{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.CYAN}Enter folder path for directory config{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Default: {os.getcwd()}{Style.RESET_ALL}")
                    folder_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip() or os.getcwd()
                    try:
                        folder_path = validate_path(folder_input)
                        saved_settings = self.config_manager.load_settings(folder_path=folder_path, scope="dir")
                        if not saved_settings:
                            print(f"{Fore.YELLOW}No directory config found.{Style.RESET_ALL}")
                    except ValueError as e:
                        print(f"{Fore.RED}{e}{Style.RESET_ALL}")

        # Resolve project root and file selection carried by the profile.
        profile_folder_path = None
        profile_selected_files = None
        edit_selection = False
        if saved_settings:
            fp = saved_settings.get('folder_path')
            # A profile must be bound to a folder path so its relative
            # selected_files can be resolved. Missing/invalid path discards
            # the profile and starts fresh.
            if not fp:
                print(f"{Fore.YELLOW}Profile is not bound to a folder path; ignoring saved settings.{Style.RESET_ALL}")
                saved_settings = None
            elif not os.path.isdir(fp):
                print(f"{Fore.YELLOW}Saved folder path no longer exists: {fp}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Starting fresh without saved settings.{Style.RESET_ALL}")
                saved_settings = None
            else:
                profile_folder_path = fp
                raw_sel = saved_settings.get('selected_files') or []
                normalized = [os.path.normpath(p) for p in raw_sel]
                if normalized:
                    missing = [p for p in normalized
                               if not os.path.exists(os.path.join(profile_folder_path, p))]
                    if missing:
                        print(f"\n{Fore.YELLOW}Warning: {len(missing)} saved file(s) no longer exist:{Style.RESET_ALL}")
                        for m in missing[:20]:
                            print(f"  - {m}")
                        if len(missing) > 20:
                            print(f"  ... and {len(missing) - 20} more")
                    profile_selected_files = [p for p in normalized if p not in missing]
                else:
                    profile_selected_files = None
                if profile_selected_files and profile_folder_path:
                    action = select_from_list(
                        ["Continue with saved files", "Edit file selection"],
                        "Use saved file selection as-is, or edit?"
                    )
                    if action is None:
                        return None
                    if action.startswith("Edit"):
                        edit_selection = True

        # Step 1: Choose mode (skipped when a saved selection is reused).
        modes = [
            "Standard Mode (with prompts and filters)",
            "Interactive File Browser (select specific files)",
            "Tree View Picker (navigate folders and select files)",
            "Drag & Drop (drop files/folders from your file manager)"
        ]

        reuse_saved_selection = bool(
            profile_folder_path and profile_selected_files and not edit_selection
        )
        mode_choice = None
        if reuse_saved_selection:
            print(f"\n{Fore.GREEN}Reusing {len(profile_selected_files)} saved file(s) from profile.{Style.RESET_ALL}")
        else:
            mode_choice = select_from_list(modes, "Select Mode:")
            if mode_choice is None:
                return None

        # Step 2: Project type selection (skipped when a saved type exists).
        project_type = None
        if saved_settings and saved_settings.get('project_type'):
            project_type = saved_settings['project_type']
            print(f"{Fore.CYAN}Using saved project type: {project_type}{Style.RESET_ALL}")
        if project_type is None:
            project_types = self.config_manager.get_all_project_types()
            scan_root = profile_folder_path or os.getcwd()
            suggested_type, confidence = self.folder_scanner.detect_project_type_advanced(scan_root)

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

        # Step 3: Folder path (or Drag & Drop selection)
        selected_files = None
        if reuse_saved_selection:
            # Profile has both a valid root and a surviving file list: use it as-is.
            folder_path = profile_folder_path
            selected_files = list(profile_selected_files)
        elif mode_choice == modes[3]:
            if not DragDropSelector.is_available():
                print(f"{Fore.RED}Drag & Drop mode requires 'tkinterdnd2'.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Install it with: pip install tkinterdnd2{Style.RESET_ALL}")
                return None
            dnd = DragDropSelector(config['exclude_folders'], config['exclude_extensions'])
            # When editing a profile, seed the selector with the saved files.
            seed_files = None
            if edit_selection and profile_folder_path and profile_selected_files:
                seed_files = [os.path.join(profile_folder_path, p) for p in profile_selected_files]
            dnd_result = dnd.browse(initial_files=seed_files)
            if not dnd_result or not dnd_result.get('files'):
                print(f"{Fore.RED}Drag & Drop cancelled or no files selected.{Style.RESET_ALL}")
                return None
            folder_path = dnd_result['folder_path']
            selected_files = dnd_result['files']
            print(f"\n{Fore.GREEN}Selected {len(selected_files)} files from {folder_path}{Style.RESET_ALL}")
        elif edit_selection and profile_folder_path:
            # Editing a profile: reuse the saved root without re-prompting.
            folder_path = profile_folder_path
            print(f"{Fore.CYAN}Using saved project root: {folder_path}{Style.RESET_ALL}")
        else:
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
        if selected_files is not None:
            # Reused from profile or provided by Drag & Drop: also reuse saved
            # filters so the user is not prompted again outside Edit mode.
            filter_folder = saved_settings.get('filter_folder') if saved_settings else None
            keyword = saved_settings.get('keyword') if saved_settings else None
            regex = saved_settings.get('regex') if saved_settings else None
            min_size = saved_settings.get('min_size', 0) if saved_settings else 0
            modified_after = None
            if saved_settings and saved_settings.get('modified_after'):
                try:
                    modified_after = datetime.datetime.fromisoformat(saved_settings['modified_after'])
                except (TypeError, ValueError):
                    modified_after = None
        elif mode_choice == modes[1]:
            file_browser = FileBrowser(config['exclude_folders'], config['exclude_extensions'])
            initial = profile_selected_files if (edit_selection and profile_selected_files) else None
            selected_files = file_browser.browse(folder_path, initial_selected=initial)
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
            initial = profile_selected_files if (edit_selection and profile_selected_files) else None
            selected_files = tree_browser.browse(folder_path, initial_selected=initial)
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

            # When editing a profile, keep the saved set as a starting point.
            if edit_selection and profile_selected_files:
                selected_files = list(profile_selected_files)

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

        # Step 5-8: When reusing a saved profile without edits, take remaining
        # options straight from the profile so the user is not prompted again.
        if reuse_saved_selection:
            selected_prompt_keys = saved_settings.get('prompt_keys') or []
            combined_prompt = ""
            for key in selected_prompt_keys:
                if key in PROMPT_TEMPLATES:
                    combined_prompt += PROMPT_TEMPLATES[key]['template'] + "\n\n"
            output_format = saved_settings.get('output_format') or "txt"
            minify = bool(saved_settings.get('minify'))
            copy_to_clipboard = bool(saved_settings.get('copy_to_clipboard'))
        else:
            # Step 5: Prompt template selection
            selected_prompt_keys = self.select_prompts(saved_settings=saved_settings)

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
            if saved_settings and saved_settings.get('output_format'):
                output_format = saved_settings['output_format']

            # Step 7: Minify option
            minify_options = ["Yes - Minify content (reduce size)", "No - Keep original content"]
            minify_choice = select_from_list(minify_options, "Enable Minification?")
            minify = (minify_choice == minify_options[0])
            if saved_settings and saved_settings.get('minify') is not None:
                minify = bool(saved_settings['minify'])

            # Step 8: Copy to clipboard
            clipboard_options = ["Yes - Copy to clipboard", "No"]
            clipboard_choice = select_from_list(clipboard_options, "Copy to Clipboard?")
            copy_to_clipboard = (clipboard_choice == clipboard_options[0])
            if saved_settings and saved_settings.get('copy_to_clipboard') is not None:
                copy_to_clipboard = bool(saved_settings['copy_to_clipboard'])

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
            'prompt_keys': selected_prompt_keys or [],
            'selected_files': selected_files,
            'split_preference': saved_settings.get('split_preference') if saved_settings else None,
            # When the user chose to edit the profile, do not pass the saved
            # split configuration back to main.py - the splitter will prompt
            # again so split settings can be revised alongside file selection.
            'split_settings': saved_settings.get('split_settings') if (saved_settings and not edit_selection) else None,
            # True when a profile was loaded and used verbatim with no edits;
            # main.py uses this to skip the redundant save prompt.
            'profile_unchanged': reuse_saved_selection,
            'saved_profile_name': None,
            'saved_scope': None
        }
