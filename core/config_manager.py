# core/config_manager.py
"""Configuration management module."""

import os
import json
import logging
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
    
    def save_profile(self, profile_name, settings):
        """Save user profile settings."""
        profiles_path = os.path.join(os.path.dirname(self.config_path), "profiles.json")
        profiles = {}
        
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            except Exception:
                pass
        
        profiles[profile_name] = settings
        
        try:
            with open(profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            logging.info(f"Profile '{profile_name}' saved successfully")
            return True
        except Exception as e:
            logging.error(f"Could not save profile: {e}")
            return False
    
    def load_profile(self, profile_name):
        """Load user profile settings."""
        profiles_path = os.path.join(os.path.dirname(self.config_path), "profiles.json")
        
        if not os.path.exists(profiles_path):
            return None
        
        try:
            with open(profiles_path, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            return profiles.get(profile_name)
        except Exception as e:
            logging.error(f"Could not load profile: {e}")
            return None
    
    def list_profiles(self):
        """List all saved profiles."""
        profiles_path = os.path.join(os.path.dirname(self.config_path), "profiles.json")
        
        if not os.path.exists(profiles_path):
            return []
        
        try:
            with open(profiles_path, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            return list(profiles.keys())
        except Exception:
            return []