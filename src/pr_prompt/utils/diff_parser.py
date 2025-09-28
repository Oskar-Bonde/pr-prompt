from dataclasses import dataclass
from enum import Enum
from typing import Optional

from git import Diff, DiffIndex, IndexObject

from .file_filters import FileFilter
from .markdown_parser import get_markdown_content


class ChangeType(Enum):
    ADDED = "Added"
    DELETED = "Deleted"
    COPIED = "Copied"
    RENAMED = "Renamed"
    RENAMED_AND_MODIFIED = "Renamed and modified"
    MODIFIED = "Modified"


@dataclass
class DiffFile:
    path: str
    change_type_enum: ChangeType
    content: str
    rename_from: Optional[str]

    @property
    def change_type(self) -> str:
        return self.change_type_enum.value

    @property
    def change_indicator(self) -> str:
        """Return single-letter change indicator for compact display."""
        status_map = {
            ChangeType.ADDED: "A",
            ChangeType.DELETED: "D",
            ChangeType.COPIED: "C",
            ChangeType.RENAMED: "R",
            ChangeType.RENAMED_AND_MODIFIED: "R",
            ChangeType.MODIFIED: "M",
        }
        return status_map[self.change_type_enum]


def get_diff_files(
    diffs: DiffIndex[Diff], blacklist_patterns: list[str]
) -> dict[str, DiffFile]:
    """Convert GitPython Diff objects to DiffFile objects."""
    diff_files = {}

    for diff in diffs:
        file_path = diff.b_path or diff.a_path
        if file_path:
            is_blacklisted = FileFilter.is_match(file_path, blacklist_patterns)

            change_type = get_change_type(diff)
            content_parts = get_content_parts(
                diff, change_type, is_blacklisted=is_blacklisted
            )
            content = "\n".join(content_parts)

            diff_files[file_path] = DiffFile(
                path=file_path,
                change_type_enum=change_type,
                content=content,
                rename_from=diff.rename_from,
            )
    return diff_files


def get_change_type(diff: Diff) -> ChangeType:
    if diff.new_file:
        return ChangeType.ADDED
    if diff.deleted_file:
        return ChangeType.DELETED
    if diff.copied_file:
        return ChangeType.COPIED
    if diff.renamed_file:
        if diff.a_blob and diff.b_blob and diff.a_blob.hexsha != diff.b_blob.hexsha:
            return ChangeType.RENAMED_AND_MODIFIED
        return ChangeType.RENAMED
    return ChangeType.MODIFIED


def get_content_parts(
    diff: Diff, change_type: ChangeType, *, is_blacklisted: bool
) -> list[str]:
    """Get raw content from diff object."""
    content_parts = []

    if diff.renamed_file and diff.rename_from and diff.rename_to:
        content_parts.append(
            f"File renamed from {diff.rename_from!r} to {diff.rename_to!r}"
        )

    if change_type == ChangeType.RENAMED:
        return content_parts

    if is_blacklisted:
        content_parts.append("[Diff ignored]")
        return content_parts

    if change_type == ChangeType.ADDED and diff.b_blob and diff.b_path:
        content = read_blob(diff.b_blob)
        content_parts.append(get_markdown_content(diff.b_path, content))

    elif change_type == ChangeType.DELETED and diff.a_blob and diff.a_path:
        content = read_blob(diff.a_blob)
        content_parts.append(get_markdown_content(diff.a_path, content))

    elif diff.diff:
        content_parts.append("```diff")
        diff_content = read_diff(diff)
        content_parts.append(f"{diff_content}```")

    return content_parts


def read_blob(blob: IndexObject) -> str:
    try:
        blob_data: bytes = blob.data_stream.read()
        file_content = blob_data.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        return "[Binary file]"
    else:
        return file_content


def read_diff(diff: Diff) -> str:
    if diff.diff is None:
        return ""
    return (
        diff.diff.decode("utf-8", errors="replace")
        if isinstance(diff.diff, bytes)
        else diff.diff
    )
