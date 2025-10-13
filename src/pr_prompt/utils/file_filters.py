import fnmatch


class FileFilter:
    """Utility class for filtering files based on patterns."""

    @staticmethod
    def is_match(file_path: str, patterns: list[str]) -> bool:
        """Check if a file path matches any of the given patterns."""
        if not patterns:
            return False
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in patterns)

    @staticmethod
    def include(files: list[str], patterns: list[str]) -> list[str]:
        """Return sorted files matching any of the given patterns."""
        if not patterns:
            return []
        return sorted(file for file in files if FileFilter.is_match(file, patterns))

    @staticmethod
    def exclude(files: list[str], patterns: list[str]) -> list[str]:
        """Return sorted files **not** matching any of the given patterns."""
        if not patterns:
            return sorted(files)
        return sorted(file for file in files if not FileFilter.is_match(file, patterns))
