# utils/git_utils.py
"""Git utilities for cloning remote repositories."""

import os
import shutil
import logging
import git


def clone_remote_repo(remote_url, temp_dir="temp_repo"):
    """Clone a remote git repository to a temporary directory."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    try:
        logging.info(f"Cloning repository: {remote_url}")
        git.Repo.clone_from(remote_url, temp_dir)
        return temp_dir
    except Exception as e:
        logging.error(f"Failed to clone repository: {e}")
        raise