import pytest
import os
import json
from core.config_manager import ConfigManager, DEFAULT_SETTINGS_KEYS


def test_save_and_load_system_profile(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    settings = {
        "project_type": "python",
        "output_format": "md",
        "minify": True,
        "copy_to_clipboard": False,
        "selected_files": ["core/__init__.py"],
        "prompt_keys": ["code_review"],
        "split_preference": "simple",
        "split_settings": {"strategy": "hybrid", "max_files": 10}
    }
    
    assert manager.save_settings("test-profile", settings, scope="system") is True
    loaded = manager.load_settings(profile_name="test-profile", scope="system")
    
    assert loaded is not None
    assert loaded["project_type"] == "python"
    assert loaded["output_format"] == "md"
    assert loaded["minify"] is True
    assert loaded["copy_to_clipboard"] is False
    assert loaded["selected_files"] == ["core/__init__.py"]
    assert loaded["prompt_keys"] == ["code_review"]
    assert loaded["split_preference"] == "simple"
    assert loaded["split_settings"] == {"strategy": "hybrid", "max_files": 10}


def test_save_and_load_dir_settings(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    settings = {
        "project_type": "nodejs",
        "output_format": "json",
        "minify": False,
        "copy_to_clipboard": True
    }
    
    assert manager.save_settings("default", settings, scope="dir", folder_path=str(project_dir)) is True
    loaded = manager.load_settings(folder_path=str(project_dir), scope="dir")
    
    assert loaded is not None
    assert loaded["project_type"] == "nodejs"
    assert loaded["output_format"] == "json"
    assert loaded["minify"] is False
    assert loaded["copy_to_clipboard"] is True


def test_dir_settings_override_system_profile(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    system_settings = {
        "project_type": "python",
        "output_format": "md",
        "minify": True
    }
    manager.save_settings("sys-profile", system_settings, scope="system")
    
    dir_settings = {
        "output_format": "html",
        "minify": False
    }
    manager.save_settings("default", dir_settings, scope="dir", folder_path=str(project_dir))
    
    loaded = manager.load_settings(profile_name="sys-profile", folder_path=str(project_dir))
    
    assert loaded is not None
    assert loaded["project_type"] == "python"
    assert loaded["output_format"] == "html"
    assert loaded["minify"] is False


def test_list_profiles(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    assert manager.list_profiles() == []
    
    manager.save_settings("profile1", {"output_format": "txt"}, scope="system")
    manager.save_settings("profile2", {"output_format": "md"}, scope="system")
    
    profiles = manager.list_profiles()
    assert "profile1" in profiles
    assert "profile2" in profiles


def test_list_dir_settings(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    assert manager.list_dir_settings(str(project_dir)) == []
    
    manager.save_settings("default", {"output_format": "txt"}, scope="dir", folder_path=str(project_dir))
    manager.save_settings("alt", {"output_format": "md"}, scope="dir", folder_path=str(project_dir))
    
    settings = manager.list_dir_settings(str(project_dir))
    assert "default" in settings
    assert "alt" in settings


def test_load_nonexistent_profile_returns_none(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    assert manager.load_settings(profile_name="nonexistent", scope="system") is None


def test_settings_only_preserve_known_keys(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    settings = {
        "project_type": "python",
        "output_format": "md",
        "unknown_key": "should-not-be-saved"
    }
    
    manager.save_settings("test", settings, scope="system")
    loaded = manager.load_settings(profile_name="test", scope="system")
    
    assert "unknown_key" not in loaded
    assert loaded["project_type"] == "python"


def test_backward_compatible_save_profile(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"projects": {"generic": {}}}))
    manager = ConfigManager(str(config_path))
    
    assert manager.save_profile("legacy-profile", {"output_format": "json"}) is True
    loaded = manager.load_profile("legacy-profile")
    
    assert loaded is not None
    assert loaded["output_format"] == "json"
