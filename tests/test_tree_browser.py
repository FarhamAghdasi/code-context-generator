import pytest
import os
from cli.file_browser import TreeFileBrowser, TreeNode


def _create_tree(tmp_path):
    core = tmp_path / "core"
    core.mkdir()
    cli = tmp_path / "cli"
    cli.mkdir()
    (tmp_path / "main.py").write_text("print('main')")
    (core / "__init__.py").write_text("")
    (core / "config.py").write_text("")
    (cli / "__init__.py").write_text("")
    (cli / "browser.py").write_text("")
    return str(tmp_path)


def test_build_tree_returns_correct_structure(tmp_path):
    folder = _create_tree(tmp_path)
    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    names = [node.name for node in root.children]
    assert "main.py" in names
    assert "core" in names
    assert "cli" in names


def test_build_tree_uses_full_relative_paths(tmp_path):
    folder = _create_tree(tmp_path)
    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    core = next(node for node in root.children if node.name == "core")
    cli = next(node for node in root.children if node.name == "cli")

    core_init = next(node for node in core.children if node.name == "__init__.py")
    cli_init = next(node for node in cli.children if node.name == "__init__.py")

    assert core_init.path == os.path.join("core", "__init__.py")
    assert cli_init.path == os.path.join("cli", "__init__.py")
    assert core_init.path != cli_init.path


def test_excluded_folders_are_skipped(tmp_path):
    folder = str(tmp_path)
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.json").write_text("{}")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("")

    browser = TreeFileBrowser(exclude_folders=["node_modules"])
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    names = [node.name for node in root.children]
    assert "node_modules" not in names
    assert "src" in names


def test_excluded_extensions_are_skipped(tmp_path):
    folder = str(tmp_path)
    (tmp_path / "image.png").write_text("")
    (tmp_path / "script.py").write_text("")

    browser = TreeFileBrowser(exclude_extensions=[".png"])
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    names = [node.name for node in root.children]
    assert "image.png" not in names
    assert "script.py" in names


def test_select_folder_selects_all_files_in_subtree(tmp_path):
    folder = _create_tree(tmp_path)
    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    core = next(node for node in root.children if node.name == "core")
    browser._selected_files = set()
    browser._select_folder(core)

    assert os.path.join("core", "__init__.py") in browser._selected_files
    assert os.path.join("core", "config.py") in browser._selected_files


def test_deselect_folder_clears_all_files_in_subtree(tmp_path):
    folder = _create_tree(tmp_path)
    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    core = next(node for node in root.children if node.name == "core")
    browser._selected_files = {os.path.join("core", "__init__.py"), os.path.join("core", "config.py")}
    browser._deselect_folder(core)

    assert os.path.join("core", "__init__.py") not in browser._selected_files
    assert os.path.join("core", "config.py") not in browser._selected_files


def test_get_visible_nodes_returns_expanded_children(tmp_path):
    folder = _create_tree(tmp_path)
    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    core = next(node for node in root.children if node.name == "core")
    core.expanded = True

    visible = browser._get_visible_nodes(root)
    visible_paths = [node.path for node, _ in visible]

    assert "" in visible_paths
    assert "main.py" in visible_paths
    assert "core" in visible_paths
    assert os.path.join("core", "__init__.py") in visible_paths
    assert os.path.join("cli", "__init__.py") not in visible_paths


def test_empty_directory_returns_empty_list(tmp_path):
    folder = str(tmp_path)
    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    assert root.children == []


def test_symlinks_are_skipped(tmp_path):
    folder = str(tmp_path)
    (tmp_path / "real.py").write_text("")
    os.symlink(tmp_path / "real.py", tmp_path / "link.py")

    browser = TreeFileBrowser()
    root = TreeNode(name=os.path.basename(folder), path="", is_dir=True, expanded=True)
    root.children = browser._build_tree(folder)

    names = [node.name for node in root.children]
    assert "real.py" in names
    assert "link.py" not in names
