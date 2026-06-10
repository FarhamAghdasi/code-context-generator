# cli/argument_parser.py
"""Command-line argument parsing module."""

import argparse


class ArgumentParser:
    """Handles command-line argument parsing."""
    
    def __init__(self):
        """Initialize ArgumentParser with all available arguments."""
        self.parser = argparse.ArgumentParser(
            description="Enhanced project structure and file reader with interactive browser",
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._add_arguments()
    
    def _add_arguments(self):
        """Add all arguments to the parser."""
        self.parser.add_argument(
            "-C", "--custom", nargs=3,
            metavar=("FOLDER", "EXCLUDE_FOLDERS", "EXCLUDE_EXTENSIONS"),
            help="Custom mode. Format: folder_path 'folder1,folder2' '.log,.md'"
        )
        self.parser.add_argument(
            "-F", "--filter",
            help="Only include folders containing this name\nExample: --filter src",
            default=None
        )
        self.parser.add_argument(
            "-K", "--keyword",
            help="Filter files containing this keyword\nExample: --keyword import",
            default=None
        )
        self.parser.add_argument(
            "-R", "--regex",
            help="Filter files matching this regex pattern\nExample: --regex '^def\\s+\\w+'",
            default=None
        )
        self.parser.add_argument(
            "--format",
            choices=["txt", "json", "md", "html"],
            default=None,
            help="Output format: txt (plain text), json (JSON), md (Markdown), html (HTML)"
        )
        self.parser.add_argument(
            "-P", "--project-type",
            choices=["python", "nodejs", "java", "go", "csharp", "php", "generic"],
            default=None,
            help="Project type (auto-detected if not provided)"
        )
        self.parser.add_argument(
            "--remote",
            help="GitHub repository URL to clone\nExample: --remote https://github.com/user/repo",
            default=None
        )
        self.parser.add_argument(
            "--copy",
            action="store_true",
            help="Copy output to clipboard"
        )
        self.parser.add_argument(
            "--log-file",
            default="output/log.txt",
            help="Path to log file"
        )
        self.parser.add_argument(
            "--min-size",
            type=int,
            default=0,
            help="Minimum file size in bytes\nExample: --min-size 1000"
        )
        self.parser.add_argument(
            "--modified-after",
            help="Only include files modified after this date (YYYY-MM-DD)\nExample: --modified-after 2023-01-01",
            default=None
        )
        self.parser.add_argument(
            "--minify",
            action="store_true",
            help="Minify file contents to reduce size"
        )
        self.parser.add_argument(
            "--prompt",
            choices=["code_review", "documentation", "commit_messages"],
            nargs='+',
            help="Add prompt template(s) to output"
        )
    
    def parse_args(self):
        """Parse command-line arguments."""
        return self.parser.parse_args()
    
    def print_help(self):
        """Print help message."""
        self.parser.print_help()