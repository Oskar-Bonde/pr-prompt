from pathlib import Path


def build_file_tree(files: list[Path]) -> str:
    """Build a tree structure representation of the files."""
    tree: dict = {}

    for file in sorted(files):
        # Navigate through the tree, creating nodes as needed
        for part in file.parts:
            if part not in tree:
                tree[part] = {}
            tree = tree[part]

    # Convert tree to string representation
    lines: list[str] = []
    render_tree_node(tree, lines, "", is_root=True)

    return "\n".join(lines)


def render_tree_node(
    node: dict, lines: list[str], prefix: str, *, is_root: bool
) -> None:
    """Recursively render tree nodes with proper tree characters."""
    items = list(node.keys())

    for i, item in enumerate(items):
        is_last = i == len(items) - 1

        if is_root:
            # Root level items don't need tree characters
            lines.append(f"{item}/")
            next_prefix = ""
        else:
            # Use tree characters for nested items
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item}/")
            next_prefix = prefix + ("    " if is_last else "│   ")

        # Recursively render children
        if node[item]:
            render_tree_node(node[item], lines, next_prefix, is_root=False)
