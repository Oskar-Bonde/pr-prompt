from pathlib import Path

from .diff_parser import DiffFile


def build_file_tree(diff_files: dict[str, DiffFile]) -> str:
    """Build a tree structure representation of the files with change type prefixes."""
    if not diff_files:
        return "No files changed"

    tree: dict = {}

    for file in sorted(diff_files.keys()):
        parts = Path(file).parts
        current = tree

        # Navigate through the tree, creating nodes as needed
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    # Convert tree to string representation
    lines: list[str] = []
    render_tree_node(tree, lines, "", "", diff_files, is_root=True)

    return "\n".join(lines)


def render_tree_node(
    node: dict,
    lines: list[str],
    prefix: str,
    current_path: str,
    diff_files: dict[str, DiffFile],
    *,
    is_root: bool,
) -> None:
    """Recursively render tree nodes with proper tree characters and change type prefixes."""
    items = list(node.keys())

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        is_folder = bool(node[item])

        # Build the full file path
        full_path = f"{current_path}/{item}" if current_path else item

        change_prefix = (
            _get_change_prefix(full_path, diff_files) if not is_folder else "   "
        )

        if is_root:
            # Root level items don't need tree characters
            if is_folder:
                lines.append(f"   {item}/")
            else:
                lines.append(f"{change_prefix}{item}")
            next_prefix = ""
        else:
            # Use tree characters for nested items
            connector = "├── " if not is_last else "└── "
            if is_folder:
                lines.append(f"{change_prefix}{prefix}{connector}{item}/")
            else:
                lines.append(f"{change_prefix}{prefix}{connector}{item}")
            next_prefix = prefix + ("    " if is_last else "│   ")

        # Recursively render children
        if node[item]:
            render_tree_node(
                node[item], lines, next_prefix, full_path, diff_files, is_root=False
            )


def _get_change_prefix(file_path: str, diff_files: dict[str, DiffFile]) -> str:
    """Get the change type prefix for a file."""
    if file_path in diff_files:
        return diff_files[file_path].change_indicator + "  "
    return "   "
