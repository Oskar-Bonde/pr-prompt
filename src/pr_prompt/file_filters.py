"""File filtering utilities."""

import fnmatch


class FileFilter:
    """Utility class for filtering files based on patterns."""

    @staticmethod
    def exclude(files: list[str], patterns: list[str]) -> list[str]:
        """
        Return file paths that don't match any of the given patterns.

        Args:
            files: list of file path strings.
            patterns: list of glob patterns to exclude.

        Returns:
            Filtered list of file path strings.
        """
        if not patterns:
            return files

        return [
            file
            for file in files
            if not any(fnmatch.fnmatch(file, pattern) for pattern in patterns)
        ]

    @staticmethod
    def match(files: list[str], patterns: list[str]) -> list[str]:
        """
        Return files matching any of the given patterns.

        Args:
            files: list of file path strings.
            patterns: list of glob patterns to match.

        Returns:
            Sorted list of unique matched files.
        """
        if not patterns:
            return []

        matched = set()
        for pattern in patterns:
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    matched.add(file)
        return sorted(matched)
