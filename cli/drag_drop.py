"""Drag-and-drop file selector for building project context."""
import os
import logging
from typing import Dict, List, Optional

from colorama import Fore, Style

try:
    import tkinter as tk
    from tkinter import messagebox
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False


class DragDropSelector:
    """
    GUI window that lets the user drag files/folders from the OS file manager.
    Expands folders recursively, respects exclusion rules, then returns a
    folder_path (common root) and a list of relative file paths.
    """

    def __init__(self, exclude_folders=None, exclude_extensions=None):
        """Initialize DragDropSelector with exclusion rules."""
        self.exclude_folders = set(exclude_folders) if exclude_folders else {'.git'}
        self.exclude_extensions = set(exclude_extensions) if exclude_extensions else {'.svg', '.jpg', '.png', '.bin'}
        self.selected_files: Optional[List[str]] = None
        self.root_folder: Optional[str] = None

    @staticmethod
    def is_available() -> bool:
        """Return True if tkinter + tkinterdnd2 are importable."""
        return DND_AVAILABLE

    def _parse_dropped_data(self, data: str) -> List[str]:
        """Parse the raw DnD payload into a list of file system paths."""
        paths: List[str] = []
        current = ""
        in_brace = False
        for ch in data:
            if ch == '{':
                in_brace = True
            elif ch == '}':
                in_brace = False
                if current:
                    paths.append(current)
                    current = ""
            elif ch == ' ' and not in_brace:
                if current:
                    paths.append(current)
                    current = ""
            else:
                current += ch
        if current:
            paths.append(current)
        return [p for p in paths if p.strip()]

    def _collect_files(self, paths: List[str]) -> List[str]:
        """Expand dropped folders into individual files, applying filters."""
        collected: List[str] = []
        for path in paths:
            path = os.path.normpath(path)
            if os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext not in self.exclude_extensions:
                    collected.append(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in self.exclude_folders]
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in self.exclude_extensions:
                            continue
                        collected.append(os.path.join(root, f))
        return collected

    def _find_common_root(self, original_paths: List[str], files: List[str]) -> Optional[str]:
        """Determine a sensible root folder for relative-path calculation."""
        if not files:
            return None
        # Single directory drop: use that directory as the root
        if len(original_paths) == 1 and os.path.isdir(original_paths[0]):
            return os.path.abspath(original_paths[0])
        try:
            dirs = [os.path.dirname(os.path.abspath(f)) for f in files]
            return os.path.commonpath(dirs)
        except ValueError:
            # Different drives on Windows or other edge case
            return os.path.dirname(os.path.abspath(files[0]))

    def browse(self) -> Optional[Dict[str, object]]:
        """
        Open the drag-and-drop window.

        Returns:
            dict with keys 'folder_path' and 'files' (relative paths), or
            None if the user cancelled / no DnD support.
        """
        if not DND_AVAILABLE:
            print(f"{Fore.RED}Drag & Drop is unavailable: 'tkinterdnd2' is not installed.{Style.RESET_ALL}")
            return None

        try:
            root = TkinterDnD.Tk()
        except Exception as e:
            logging.error(f"Failed to initialize Tk window: {e}")
            print(f"{Fore.RED}Failed to open drag-and-drop window: {e}{Style.RESET_ALL}")
            return None

        root.title("Drag & Drop - Build AI Context")
        root.geometry("680x520")
        root.configure(bg="#1e1e1e")
        root.attributes("-topmost", True)

        tk.Label(
            root, text="Drag & Drop files or folders here",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff", bg="#1e1e1e"
        ).pack(pady=(18, 4))

        tk.Label(
            root,
            text="Folders are expanded recursively. A project tree will be built from the common root.",
            font=("Segoe UI", 9),
            fg="#a0a0a0", bg="#1e1e1e"
        ).pack(pady=(0, 12))

        drop_zone = tk.Label(
            root, text="Drop files / folders here",
            font=("Segoe UI", 12),
            fg="#cccccc", bg="#2d2d2d",
            width=62, height=6,
            relief="ridge", borderwidth=2
        )
        drop_zone.pack(padx=20, pady=(0, 8))

        file_listbox = tk.Listbox(
            root, bg="#252526", fg="#d4d4d4",
            selectbackground="#094771",
            font=("Consolas", 9), height=10,
            selectmode="extended"
        )
        file_listbox.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        tk.Label(
            root,
            text="Tip: select one or more items and press DEL (or use 'Remove Selected').",
            font=("Segoe UI", 8, "italic"),
            fg="#808080", bg="#1e1e1e"
        ).pack(pady=(0, 4))

        info_label = tk.Label(
            root, text="No files dropped yet.",
            font=("Segoe UI", 9),
            fg="#a0a0a0", bg="#1e1e1e"
        )
        info_label.pack(pady=(0, 6))

        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=(0, 14))

        state: Dict[str, object] = {"files": [], "root": None, "originals": []}

        def update_view() -> None:
            file_listbox.delete(0, tk.END)
            for f in state["files"]:  # type: ignore[union-attr]
                try:
                    display = os.path.relpath(f, state["root"]) if state["root"] else f
                except ValueError:
                    display = f
                file_listbox.insert(tk.END, display)
            root_text = state["root"] or "-"
            info_label.config(text=f"{len(state['files'])} file(s)  |  Root: {root_text}")

        def on_drop(event) -> None:
            paths = self._parse_dropped_data(event.data)
            if not paths:
                return
            new_files = self._collect_files(paths)
            existing = set(state["files"])  # type: ignore[arg-type]
            originals = list(state["originals"])  # type: ignore[arg-type]
            for p in paths:
                if p not in originals:
                    originals.append(p)
            state["originals"] = originals
            files = list(state["files"])  # type: ignore[arg-type]
            for f in new_files:
                if f not in existing:
                    files.append(f)
                    existing.add(f)
            state["files"] = files
            state["root"] = self._find_common_root(originals, files)
            update_view()

        def clear_all() -> None:
            state["files"] = []
            state["originals"] = []
            state["root"] = None
            update_view()

        def remove_selected() -> None:
            """Remove highlighted entries from the pending list (does not touch disk)."""
            indices = list(file_listbox.curselection())
            if not indices:
                return
            files = list(state["files"])  # type: ignore[arg-type]
            # Delete from the end so earlier indices stay valid
            for idx in reversed(indices):
                if 0 <= idx < len(files):
                    files.pop(idx)
            state["files"] = files
            # Recompute the common root from the remaining files
            if files:
                try:
                    parents = [os.path.dirname(os.path.abspath(f)) for f in files]
                    state["root"] = os.path.commonpath(parents)
                except ValueError:
                    state["root"] = os.path.dirname(os.path.abspath(files[0]))
            else:
                state["root"] = None
            update_view()

        def _on_delete_key(event) -> str:
            """Key handler for DEL / Backspace on the listbox."""
            remove_selected()
            return "break"

        def confirm() -> None:
            if not state["files"]:
                messagebox.showwarning("No files", "Please drop at least one file or folder.")
                return
            self.selected_files = list(state["files"])  # type: ignore[arg-type]
            self.root_folder = state["root"]  # type: ignore[assignment]
            root.destroy()

        def cancel() -> None:
            self.selected_files = None
            self.root_folder = None
            root.destroy()

        drop_zone.drop_target_register(DND_FILES)
        drop_zone.dnd_bind('<<Drop>>', on_drop)
        file_listbox.drop_target_register(DND_FILES)
        file_listbox.dnd_bind('<<Drop>>', on_drop)

        # Keyboard shortcuts for removing entries
        file_listbox.bind('<Delete>', _on_delete_key)
        file_listbox.bind('<BackSpace>', _on_delete_key)

        tk.Button(
            btn_frame, text="Use These Files", command=confirm,
            bg="#0e639c", fg="white", padx=16, pady=5,
            relief="flat", activebackground="#1177bb", activeforeground="white"
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Remove Selected", command=remove_selected,
            bg="#7a3030", fg="white", padx=16, pady=5,
            relief="flat", activebackground="#9a4040", activeforeground="white"
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Clear", command=clear_all,
            bg="#3a3a3a", fg="white", padx=16, pady=5,
            relief="flat", activebackground="#4a4a4a", activeforeground="white"
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Cancel", command=cancel,
            bg="#3a3a3a", fg="white", padx=16, pady=5,
            relief="flat", activebackground="#4a4a4a", activeforeground="white"
        ).pack(side="left", padx=4)

        root.protocol("WM_DELETE_WINDOW", cancel)
        root.mainloop()

        if self.selected_files is None or not self.selected_files:
            return None

        # Convert absolute paths to relative paths from root_folder
        if self.root_folder:
            rel_files: List[str] = []
            for f in self.selected_files:
                try:
                    rel_files.append(os.path.relpath(f, self.root_folder))
                except ValueError:
                    rel_files.append(f)
        else:
            rel_files = list(self.selected_files)

        return {
            'folder_path': self.root_folder or os.path.dirname(self.selected_files[0]),
            'files': rel_files
        }