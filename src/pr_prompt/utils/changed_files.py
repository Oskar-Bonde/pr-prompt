from .diff_parser import DiffFile


def get_changed_files(diff_files: dict[str, DiffFile]) -> str:
    """Build a flat list of changed files with change type indicators."""
    if not diff_files:
        return "No files changed"

    lines = [
        f"{df.change_indicator} {_format_path(path, df)}"
        for path, df in sorted(diff_files.items())
    ]
    return "\n".join(lines)


def _format_path(path: str, diff_file: DiffFile) -> str:
    """Format the path, showing the original name for renamed files."""
    if diff_file.rename_from:
        return f"{diff_file.rename_from} -> {path}"
    return path
