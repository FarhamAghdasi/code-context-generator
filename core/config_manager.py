# core/config_manager.py
"""Configuration management module."""

import os
import json
import logging
import datetime
from colorama import Fore


# Project defaults for different project types
PROJECT_DEFAULTS = {
    "python": {
        "exclude_folders": [".git", ".venv", "__pycache__", "venv", "env", ".pytest_cache", ".mypy_cache", "dist", "build", "*.egg-info"],
        "exclude_extensions": [".svg", ".pyc", ".jpg", ".png", ".bin", ".pyo", ".pyd", ".so", ".dll"],
        "filter_folder": None,
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    },
    "nodejs": {
        "exclude_folders": [".git", "node_modules", "dist", "build", ".next", "coverage", ".nuxt"],
        "exclude_extensions": [".svg", ".log", ".jpg", ".png", ".bin", ".map", ".lock"],
        "filter_folder": "src",
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    },
    "java": {
        "exclude_folders": [".git", "target", ".idea", "build", "out", ".gradle"],
        "exclude_extensions": [".svg", ".class", ".jpg", ".png", ".bin", ".jar", ".war"],
        "filter_folder": "src",
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    },
    "go": {
        "exclude_folders": [".git", "vendor", "bin"],
        "exclude_extensions": [".svg", ".jpg", ".png", ".bin"],
        "filter_folder": None,
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    },
    "csharp": {
        "exclude_folders": [".git", "bin", "obj", "packages", ".vs"],
        "exclude_extensions": [".svg", ".dll", ".exe", ".pdb", ".jpg", ".png"],
        "filter_folder": None,
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    },
    "php": {
        "exclude_folders": [".git", "vendor", "cache", "storage"],
        "exclude_extensions": [".svg", ".jpg", ".png", ".bin"],
        "filter_folder": None,
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    },
    "generic": {
        "exclude_folders": [".git"],
        "exclude_extensions": [".svg", ".jpg", ".png", ".bin"],
        "filter_folder": None,
        "keyword": None,
        "regex": None,
        "output_format": "txt",
        "min_size": 0,
        "modified_after": None
    }
}

PROJECT_COLORS = {
    "python": Fore.MAGENTA,
    "nodejs": Fore.YELLOW,
    "java": Fore.GREEN,
    "go": Fore.BLUE,
    "csharp": Fore.CYAN,
    "php": Fore.LIGHTMAGENTA_EX,
    "generic": Fore.WHITE
}

DEFAULT_SETTINGS_KEYS = {
    "project_type",
    "output_format",
    "minify",
    "copy_to_clipboard",
    "selected_files",
    "prompt_keys",
    "split_preference",
    "split_settings",
    "filter_folder",
    "keyword",
    "regex",
    "min_size",
    "modified_after"
}


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_path=None):
        """Initialize ConfigManager with optional config file path."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        self.config_path = config_path
        self.config = {"projects": PROJECT_DEFAULTS.copy()}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.json."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception as e:
                logging.warning(f"Could not load config.json: {e}")
    
    def get_project_config(self, project_type="generic"):
        """Get configuration for a specific project type."""
        return self.config["projects"].get(project_type, PROJECT_DEFAULTS["generic"])
    
    def get_default_config(self, project_type):
        """Get default configuration for a project type."""
        return PROJECT_DEFAULTS.get(project_type, PROJECT_DEFAULTS["generic"])
    
    def get_all_project_types(self):
        """Get list of all project types."""
        return list(PROJECT_DEFAULTS.keys())
    
    def get_project_color(self, project_type):
        """Get color for a project type."""
        return PROJECT_COLORS.get(project_type, Fore.WHITE)
    
    def _profiles_path(self):
        return os.path.join(os.path.dirname(self.config_path), "profiles.json")
    
    def _dir_settings_path(self, folder_path):
        return os.path.join(folder_path, ".code-context-settings.json")
    
    def save_profile(self, profile_name, settings):
        """Save user profile settings."""
        return self.save_settings(profile_name, settings, scope="system")
    
    def load_profile(self, profile_name):
        """Load user profile settings."""
        return self.load_settings(profile_name=profile_name, scope="system")
    
    def list_profiles(self):
        """List all saved profiles."""
        return self.list_settings(scope="system")
    
    def save_settings(self, profile_name, settings, scope="system", folder_path=None):
        """Save settings to a profile or directory config."""
        if scope == "dir":
            if not folder_path or not os.path.isdir(folder_path):
                logging.error("Invalid folder_path for dir-scoped settings")
                return False
            target_path = self._dir_settings_path(folder_path)
            payload = {"name": profile_name, "scope": "dir", "folder_path": folder_path}
        else:
            target_path = self._profiles_path()
            payload = {"name": profile_name, "scope": "system"}
        
        payload.update({k: settings.get(k) for k in DEFAULT_SETTINGS_KEYS if k in settings})
        payload["saved_at"] = datetime.datetime.now().isoformat()
        
        try:
            existing = {}
            if os.path.exists(target_path):
                with open(target_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            existing[profile_name] = payload
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            logging.info(f"Settings '{profile_name}' saved to {target_path}")
            return True
        except Exception as e:
            logging.error(f"Could not save settings: {e}")
            return False
    
    def load_settings(self, profile_name=None, folder_path=None, scope=None):
        """Load settings with fallback: dir override -> system profile -> config.json defaults."""
        dir_settings = None
        system_profile = None
        dir_profile_data = None
        
        if scope is None or scope == "dir":
            if folder_path and os.path.isdir(folder_path):
                dir_path = self._dir_settings_path(folder_path)
                if os.path.exists(dir_path):
                    try:
                        with open(dir_path, 'r', encoding='utf-8') as f:
                            dir_profile_data = json.load(f)
                        if scope == "dir" and profile_name:
                            dir_settings = dir_profile_data.get(profile_name)
                        elif scope == "dir" and not profile_name:
                            dir_settings = next(iter(dir_profile_data.values())) if dir_profile_data else None
                    except Exception as e:
                        logging.warning(f"Could not load dir settings: {e}")
        
        if scope is None or scope == "system":
            if profile_name:
                try:
                    profiles_path = self._profiles_path()
                    if os.path.exists(profiles_path):
                        with open(profiles_path, 'r', encoding='utf-8') as f:
                            profiles = json.load(f)
                            system_profile = profiles.get(profile_name)
                except Exception as e:
                    logging.warning(f"Could not load system profile: {e}")
        
        merged = {}
        if system_profile:
            merged.update(system_profile)
        if dir_settings:
            merged.update(dir_settings)
        elif dir_profile_data and scope != "dir":
            merged.update(next(iter(dir_profile_data.values())))
        
        if not merged:
            return None
        
        return {k: merged.get(k) for k in DEFAULT_SETTINGS_KEYS if k in merged}
    
    def list_settings(self, scope="system"):
        """List available saved settings."""
        if scope == "system":
            path = self._profiles_path()
        else:
            path = None
            logging.warning("list_settings for dir scope requires folder_path; use list_dir_settings instead")
            return []
        
        if not path or not os.path.exists(path):
            return []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return list(data.keys())
        except Exception:
            return []
    
    def list_dir_settings(self, folder_path):
        """List directory-scoped settings names."""
        path = self._dir_settings_path(folder_path)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return list(data.keys())
        except Exception:
            return []