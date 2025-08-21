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
    def match(files: list[str], patterns: list[str]) -> list[str]:
        """Return sorted files matching any of the given patterns."""
        if not patterns:
            return []

        matched = set()
        for pattern in patterns:
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    matched.add(file)
        return sorted(matched)
