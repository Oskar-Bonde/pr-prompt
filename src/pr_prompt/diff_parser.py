import sys
from dataclasses import dataclass
from enum import Enum

from git import Diff, DiffIndex

from .file_filters import FileFilter

defenc = sys.getfilesystemencoding()


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

    @property
    def change_type(self) -> str:
        return self.change_type_enum.value


def get_diff_files(
    diffs: DiffIndex[Diff], blacklist_patterns: list[str]
) -> dict[str, DiffFile]:
    """Convert GitPython Diff objects to DiffFile objects."""
    diff_files = {}

    for diff in diffs:
        file_path = diff.b_path or diff.a_path
        if file_path and not FileFilter.is_match(file_path, blacklist_patterns):
            content = get_diff_content(diff)
            change_type = get_change_type(diff)
            diff_files[file_path] = DiffFile(file_path, change_type, content)
    return diff_files


def get_diff_content(diff: Diff) -> str:
    content = ""
    if diff.rename_from and diff.rename_to:
        content += f"\nfile renamed from {diff.rename_from!r} to {diff.rename_to!r}"
    if diff.diff:
        content += "\n---"
        content += (
            diff.diff.decode(defenc) if isinstance(diff.diff, bytes) else diff.diff
        )
    return content.strip()


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
