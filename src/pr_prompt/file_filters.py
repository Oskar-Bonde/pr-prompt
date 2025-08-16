"""File filtering utilities."""

import fnmatch
from pathlib import Path


class FileFilter:
    """Utility class for filtering files based on patterns."""

    @staticmethod
    def exclude(files: list[Path], patterns: list[str]) -> list[Path]:
        """
        Return Path objects that don't match any of the given patterns.

        Args:
            files: list of Path objects.
            patterns: list of glob patterns to exclude.

        Returns:
            Filtered list of Path objects.
        """
        if not patterns:
            return files

        return [
            file
            for file in files
            if not any(fnmatch.fnmatch(str(file), pattern) for pattern in patterns)
        ]

    @staticmethod
    def match(files: list[Path], patterns: list[str]) -> list[Path]:
        """
        Return files matching any of the given patterns.

        Args:
            files: list of file paths.
            patterns: list of glob patterns to match.

        Returns:
            Sorted list of unique matched files.
        """
        if not patterns:
            return []


        matched = set()
        for pattern in patterns:
            matched.update(fnmatch.filter([str(file) for file in files], pattern))
        return sorted(matched)
    
    
