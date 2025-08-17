from dataclasses import dataclass
from enum import Enum
from pathlib import Path


def parse_diff_by_files(diff: str, file_whitelist: list[Path]) -> dict[str, str]:
    """
    Parse a git diff output and extract individual file diffs.

    Returns:
        Dictionary mapping file paths to their diff content
    """
    file_diffs = {}
    current_file = None
    current_diff_lines = []

    whitelist_strings = {str(f) for f in file_whitelist}

    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            # Save previous file diff if it was in whitelist
            if current_file and current_file in whitelist_strings:
                file_diffs[current_file] = "\n".join(current_diff_lines)

            # Start new file diff
            current_diff_lines = [line]
            current_file = extract_file_path_from_diff_header(line)

        elif current_file:
            current_diff_lines.append(line)

    # Save the last file
    if current_file and current_file in whitelist_strings:
        file_diffs[current_file] = "\n".join(current_diff_lines)

    return file_diffs


def extract_file_path_from_diff_header(diff_header: str) -> str:
    """
    Extract the target file path from a git diff header.

    Args:
        diff_header: Line like "diff --git a/old.py b/new.py"
    """
    parts = diff_header.split()

    min_parts = 4
    if len(parts) < min_parts:
        msg = f"Invalid diff header format: {diff_header}"
        raise ValueError(msg)

    b_path = parts[3]  # b/file.py
    if not b_path.startswith("b/"):
        msg = f"Expected 'b/' prefix in diff header: {diff_header}"
        raise ValueError(msg)

    return b_path[2:]  # Remove 'b/' prefix


class DiffOperation(Enum):
    MODIFIED = "Modified"
    ADDED = "Added"
    DELETED = "Deleted"
    RENAMED = "Renamed"
    RENAMED_AND_MODIFIED = "Renamed and Modified"


@dataclass
class DiffFile:
    path: str
    operation_type: DiffOperation
    content: str


def clean_file_diffs(file_diffs: dict[str, str]) -> dict[str, DiffFile]:
    """
    Clean file diffs by removing metadata and extracting operation types.

    Args:
        file_diffs: Dictionary mapping file paths to their raw diff content

    Returns:
        Dictionary mapping file paths to cleaned diff content
    """
    cleaned_diffs = {}

    for file_path, diff_content in file_diffs.items():
        diff_file = clean_diff_content(file_path, diff_content)
        cleaned_diffs[file_path] = diff_file

    return cleaned_diffs


def clean_diff_content(file_path: str, file_diff: str) -> DiffFile:
    """
    Clean file diff by removing metadata and extracting operation type.

    Args:
        file_path: The path of the file being modified
        file_diff: Raw git diff output for a single file

    Returns:
        DiffFile with operation type and cleaned content
    """
    lines = file_diff.split("\n")
    operation_type = DiffOperation.MODIFIED  # default
    name_history = ""
    content_start_idx = 0

    for i, line in enumerate(lines):
        if line.startswith("new file mode"):
            operation_type = DiffOperation.ADDED
        elif line.startswith("deleted file mode"):
            operation_type = DiffOperation.DELETED
        elif line.startswith("similarity index") and "rename from" in file_diff:
            if "similarity index 100%" in line:
                operation_type = DiffOperation.RENAMED
            else:
                operation_type = DiffOperation.RENAMED_AND_MODIFIED
        elif line.startswith("rename from "):
            name_history = f"{line} to {file_path}"
        elif line.startswith("@@"):
            content_start_idx = i
            break

    # For pure renames (100% similarity), we don't need the content
    if operation_type == DiffOperation.RENAMED:
        return DiffFile(file_path, operation_type, name_history)

    content = extract_diff_content(lines, content_start_idx, name_history)
    return DiffFile(file_path, operation_type, content)


def extract_diff_content(
    lines: list[str], content_start_idx: int, name_history: str
) -> str:
    if content_start_idx >= len(lines):
        return ""

    cleaned_lines = lines[content_start_idx:]
    if name_history:
        cleaned_lines.insert(0, name_history)

    return "\n".join(cleaned_lines)
