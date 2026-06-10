# utils/clipboard.py
"""Clipboard utilities."""

import logging
import pyperclip


def copy_to_clipboard(content):
    """Copy content to clipboard."""
    try:
        pyperclip.copy(content)
        logging.info("Output copied to clipboard")
        return True
    except Exception as e:
        logging.error(f"Failed to copy to clipboard: {e}")
        return False