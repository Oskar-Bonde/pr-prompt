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
