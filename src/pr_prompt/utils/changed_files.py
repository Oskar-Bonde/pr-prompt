from .diff_parser import DiffFile


def get_changed_files(diff_files: dict[str, DiffFile]) -> str:
    """Build a flat list of changed files with change type indicators."""
    if not diff_files:
        return "No files changed"

    lines = [f"{df.change_indicator} {path}" for path, df in sorted(diff_files.items())]
    return "\n".join(lines)
