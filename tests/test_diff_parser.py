"""Tests for diff_parser module."""

import pytest

from pr_prompt.diff_parser import (
    DiffOperation,
    clean_diff_content,
    clean_file_diffs,
    extract_diff_content,
    extract_file_path_from_diff_header,
    parse_diff_by_files,
)


class TestExtractFilePathFromDiffHeader:
    """Test extracting file paths from diff headers."""

    def test_basic_diff_header(self) -> None:
        """Test extracting path from basic diff header."""
        header = "diff --git a/pyproject.toml b/pyproject.toml"
        result = extract_file_path_from_diff_header(header)
        assert result == "pyproject.toml"

    def test_renamed_file_header(self) -> None:
        """Test extracting path from renamed file header."""
        header = (
            "diff --git a/superpackage/dataframe.py b/superpackage/edited_dataframe.py"
        )
        result = extract_file_path_from_diff_header(header)
        assert result == "superpackage/edited_dataframe.py"

    def test_nested_path(self) -> None:
        """Test extracting nested file paths."""
        header = (
            "diff --git a/src/pr_prompt/diff_parser.py b/src/pr_prompt/diff_parser.py"
        )
        result = extract_file_path_from_diff_header(header)
        assert result == "src/pr_prompt/diff_parser.py"

    def test_invalid_header_too_few_parts(self) -> None:
        """Test error handling for invalid diff header with too few parts."""
        header = "diff --git a/file.py"
        with pytest.raises(ValueError, match="Invalid diff header format"):
            extract_file_path_from_diff_header(header)

    def test_invalid_header_missing_b_prefix(self) -> None:
        """Test error handling for missing 'b/' prefix."""
        header = "diff --git a/file.py file.py"
        with pytest.raises(ValueError, match="Expected 'b/' prefix"):
            extract_file_path_from_diff_header(header)

    def test_file_with_spaces(self) -> None:
        """Test extracting path from file with spaces in name."""
        header = "diff --git a/file with spaces.py b/file with spaces.py"
        with pytest.raises(ValueError, match="Expected 'b/' prefix in diff header"):
            extract_file_path_from_diff_header(header)


class TestParseDiffByFiles:
    """Test parsing git diff output by files."""

    def test_single_modified_file(self) -> None:
        """Test parsing diff with single modified file."""
        diff = """diff --git a/pyproject.toml b/pyproject.toml
index a8b605e888..f0b1ecbba9 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,426 +1,347 @@
-old content
+new content
"""

        file_whitelist = ["pyproject.toml"]
        result = parse_diff_by_files(diff, file_whitelist)

        assert len(result) == 1
        assert "pyproject.toml" in result
        assert (
            "diff --git a/pyproject.toml b/pyproject.toml" in result["pyproject.toml"]
        )
        assert "@@ -1,426 +1,347 @@" in result["pyproject.toml"]

    def test_multiple_files_with_whitelist(self) -> None:
        """Test parsing diff with multiple files and whitelist filtering."""
        diff = """diff --git a/file1.py b/file1.py
index 123..456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,3 @@
-old line
+new line

diff --git a/file2.py b/file2.py
index 789..abc 100644
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,2 @@
-another old line
+another new line

diff --git a/file3.py b/file3.py
index def..ghi 100644
--- a/file3.py
+++ b/file3.py
@@ -1,1 +1,1 @@
-third line
+third new line"""

        file_whitelist = ["file1.py", "file3.py"]
        result = parse_diff_by_files(diff, file_whitelist)

        assert len(result) == len(file_whitelist)
        assert "file1.py" in result
        assert "file3.py" in result
        assert "file2.py" not in result
        assert "old line" in result["file1.py"]
        assert "third line" in result["file3.py"]

    def test_renamed_file(self) -> None:
        """Test parsing diff with renamed file."""
        diff = """diff --git a/superpackage/schemas.py b/superpackage/renamed_schemas.py
similarity index 100%
rename from superpackage/schemas.py
rename to superpackage/renamed_schemas.py"""

        file_whitelist = ["superpackage/renamed_schemas.py"]
        result = parse_diff_by_files(diff, file_whitelist)

        assert len(result) == 1
        assert "superpackage/renamed_schemas.py" in result
        assert "similarity index 100%" in result["superpackage/renamed_schemas.py"]

    def test_empty_whitelist(self) -> None:
        """Test parsing with empty whitelist returns no files."""
        diff = """diff --git a/file1.py b/file1.py
index 123..456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-old
+new"""

        result = parse_diff_by_files(diff, [])
        assert len(result) == 0

    def test_no_matching_files(self) -> None:
        """Test parsing with whitelist that doesn't match any files."""
        diff = """diff --git a/file1.py b/file1.py
index 123..456 100644"""

        file_whitelist = ["file2.py"]
        result = parse_diff_by_files(diff, file_whitelist)
        assert len(result) == 0


class TestCleanDiffContent:
    """Test cleaning individual diff content."""

    def test_modified_file(self) -> None:
        """Test cleaning modified file diff."""
        diff = """diff --git a/pyproject.toml b/pyproject.toml
index a8b605e888..f0b1ecbba9 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,426 +1,347 @@
-old content
+new content"""

        result = clean_diff_content("pyproject.toml", diff)

        assert result.path == "pyproject.toml"
        assert result.operation_type == DiffOperation.MODIFIED
        assert "@@ -1,426 +1,347 @@" in result.content
        assert "old content" in result.content
        assert "new content" in result.content

    def test_added_file(self) -> None:
        """Test cleaning added file diff."""
        diff = """diff --git a/superpackage/use_pr_prompt.py b/superpackage/use_pr_prompt.py
new file mode 100644
index 0000000000..f90a4b9cfd
--- /dev/null
+++ b/superpackage/use_pr_prompt.py
@@ -0,0 +1,16 @@
+from pr_prompt import get_pr_prompt"""

        result = clean_diff_content("superpackage/use_pr_prompt.py", diff)

        assert result.path == "superpackage/use_pr_prompt.py"
        assert result.operation_type == DiffOperation.ADDED
        assert "@@ -0,0 +1,16 @@" in result.content
        assert "from pr_prompt import get_pr_prompt" in result.content

    def test_deleted_file(self) -> None:
        """Test cleaning deleted file diff."""
        diff = """diff --git a/superpackage/legacy.py b/superpackage/legacy.py
deleted file mode 100644
index 06fc527582..0000000000
--- a/superpackage/legacy.py
+++ /dev/null
@@ -1,41 +0,0 @@
-old content
+new content"""

        result = clean_diff_content("superpackage/legacy.py", diff)

        assert result.path == "superpackage/legacy.py"
        assert result.operation_type == DiffOperation.DELETED
        assert "@@ -1,41 +0,0 @@" in result.content
        assert "+new content" in result.content

    def test_renamed_file_only(self) -> None:
        """Test cleaning pure rename (100% similarity)."""
        diff = """diff --git a/superpackage/schemas.py b/superpackage/renamed_schemas.py
similarity index 100%
rename from superpackage/schemas.py
rename to superpackage/renamed_schemas.py"""

        result = clean_diff_content("superpackage/renamed_schemas.py", diff)

        assert result.path == "superpackage/renamed_schemas.py"
        assert result.operation_type == DiffOperation.RENAMED
        assert (
            "rename from superpackage/schemas.py to superpackage/renamed_schemas.py"
            in result.content
        )

    def test_renamed_and_modified_file(self) -> None:
        """Test cleaning renamed and modified file."""
        diff = """diff --git a/superpackage/dataframe.py b/superpackage/edited_dataframe.py
similarity index 92%
rename from superpackage/dataframe.py
rename to superpackage/edited_dataframe.py
index 5f3c0dc779..c927721ee9 100644
--- a/superpackage/dataframe.py
+++ b/superpackage/edited_dataframe.py
@@ -1,57 +1,57 @@
-old code
+new code"""

        result = clean_diff_content("superpackage/edited_dataframe.py", diff)

        assert result.path == "superpackage/edited_dataframe.py"
        assert result.operation_type == DiffOperation.RENAMED_AND_MODIFIED
        assert (
            "rename from superpackage/dataframe.py to superpackage/edited_dataframe.py"
            in result.content
        )
        assert "@@ -1,57 +1,57 @@" in result.content
        assert "old code" in result.content
        assert "new code" in result.content

    def test_diff_without_content_section(self) -> None:
        """Test handling diff without @@ content section."""
        diff = """diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py"""

        result = clean_diff_content("file.py", diff)

        assert result.path == "file.py"
        assert result.operation_type == DiffOperation.MODIFIED
        assert result.content == diff


class TestExtractDiffContent:
    """Test extracting diff content from lines."""

    def test_extract_from_middle(self) -> None:
        """Test extracting content starting from middle of lines."""
        lines = [
            "diff --git a/file.py b/file.py",
            "index 123..456 100644",
            "--- a/file.py",
            "+++ b/file.py",
            "@@ -1,3 +1,3 @@",
            " unchanged line",
            "-old line",
            "+new line",
            " another unchanged",
        ]

        result = extract_diff_content(lines, 4, "")

        expected = """@@ -1,3 +1,3 @@
 unchanged line
-old line
+new line
 another unchanged"""
        assert result == expected

    def test_extract_with_name_history(self) -> None:
        """Test extracting content with name history."""
        lines = [
            "diff --git a/old.py b/new.py",
            "@@ -1,2 +1,2 @@",
            "-old content",
            "+new content",
        ]

        result = extract_diff_content(lines, 1, "rename from old.py to new.py")

        expected = """rename from old.py to new.py
@@ -1,2 +1,2 @@
-old content
+new content"""
        assert result == expected

    def test_extract_beyond_bounds(self) -> None:
        """Test extracting when start index is beyond bounds."""
        lines = ["line1", "line2"]
        result = extract_diff_content(lines, 5, "")
        assert result == ""

    def test_extract_empty_name_history(self) -> None:
        """Test extracting without name history."""
        lines = ["@@ -1,1 +1,1 @@", "-old", "+new"]
        result = extract_diff_content(lines, 0, "")

        expected = """@@ -1,1 +1,1 @@
-old
+new"""
        assert result == expected


class TestCleanFileDiffs:
    """Test cleaning multiple file diffs."""

    def test_clean_multiple_files(self) -> None:
        """Test cleaning multiple file diffs."""
        file_diffs = {
            "file1.py": """diff --git a/file1.py b/file1.py
index 123..456 100644
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,1 @@
-old
+new""",
            "file2.py": """diff --git a/file2.py b/file2.py
new file mode 100644
index 000..789 100644
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,1 @@
+added content""",
        }

        result = clean_file_diffs(file_diffs)
        files_in_diff = 2
        assert len(result) == files_in_diff
        assert "file1.py" in result
        assert "file2.py" in result

        assert result["file1.py"].operation_type == DiffOperation.MODIFIED
        assert result["file2.py"].operation_type == DiffOperation.ADDED

        assert "old" in result["file1.py"].content
        assert "new" in result["file1.py"].content
        assert "added content" in result["file2.py"].content

    def test_clean_empty_dict(self) -> None:
        """Test cleaning empty file diffs dictionary."""
        result = clean_file_diffs({})
        assert len(result) == 0

    def test_all_operation_types(self) -> None:
        """Test that all operation types are correctly identified."""
        file_diffs = {
            "modified.py": """diff --git a/modified.py b/modified.py
index 123..456 100644
--- a/modified.py
+++ b/modified.py
@@ -1,1 +1,1 @@
-old
+new""",
            "added.py": """diff --git a/added.py b/added.py
new file mode 100644
index 000..789 100644
--- /dev/null
+++ b/added.py
@@ -0,0 +1,1 @@
+new file""",
            "deleted.py": """diff --git a/deleted.py b/deleted.py
deleted file mode 100644
index 789..000 100644
--- a/deleted.py
+++ /dev/null
@@ -1,1 +0,0 @@
-deleted file""",
            "renamed.py": """diff --git a/old.py b/renamed.py
similarity index 100%
rename from old.py
rename to renamed.py""",
            "renamed_modified.py": """diff --git a/old.py b/renamed_modified.py
similarity index 95%
rename from old.py
rename to renamed_modified.py
index 123..456 100644
--- a/old.py
+++ b/renamed_modified.py
@@ -1,1 +1,1 @@
-old
+new""",
        }

        result = clean_file_diffs(file_diffs)

        assert result["modified.py"].operation_type == DiffOperation.MODIFIED
        assert result["added.py"].operation_type == DiffOperation.ADDED
        assert result["deleted.py"].operation_type == DiffOperation.DELETED
        assert result["renamed.py"].operation_type == DiffOperation.RENAMED
        assert (
            result["renamed_modified.py"].operation_type
            == DiffOperation.RENAMED_AND_MODIFIED
        )


class TestFailureCases:
    """Test cases that should fail or handle edge cases."""

    def test_malformed_diff_header_causes_failure(self) -> None:
        """Test that malformed diff headers cause appropriate failures."""
        # This test demonstrates a case that will fail
        malformed_diff = """diff --git malformed header
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,1 +1,1 @@
-old
+new"""

        file_whitelist = ["file.py"]

        # This should raise an exception due to malformed header
        with pytest.raises(ValueError, match="Expected 'b/' prefix in diff header"):
            parse_diff_by_files(malformed_diff, file_whitelist)

    def test_empty_diff_string(self) -> None:
        """Test handling of empty diff string."""
        result = parse_diff_by_files("", ["any_file.py"])
        assert len(result) == 0

    def test_diff_header_only_no_content(self) -> None:
        """Test diff with header but no content."""
        diff = "diff --git a/file.py b/file.py"
        file_whitelist = ["file.py"]

        result = parse_diff_by_files(diff, file_whitelist)
        assert len(result) == 1
        assert result["file.py"] == "diff --git a/file.py b/file.py"

    def test_invalid_similarity_index_handling(self) -> None:
        """Test handling of invalid similarity index format."""
        diff = """diff --git a/old.py b/new.py
similarity index invalid%
rename from old.py
rename to new.py"""

        # Should still parse but treat as regular rename
        result = clean_diff_content("new.py", diff)
        # Since similarity index is not "100%", it should be treated as renamed and modified
        assert result.operation_type == DiffOperation.RENAMED_AND_MODIFIED

    def test_diff_with_binary_file_marker(self) -> None:
        """Test handling of binary file diffs."""
        diff = """diff --git a/image.png b/image.png
index 123..456 100644
GIT binary patch
delta 123
zcmV binary data here
delta 456
zcmV more binary data"""

        result = clean_diff_content("image.png", diff)
        assert result.operation_type == DiffOperation.MODIFIED
        assert "binary patch" in result.content

    def test_very_long_file_path(self) -> None:
        """Test handling of very long file paths."""
        long_path = "a/" + "very_long_directory_name/" * 10 + "file.py"
        header = f"diff --git {long_path} b/{long_path[2:]}"

        result = extract_file_path_from_diff_header(header)
        assert result == long_path[2:]  # Remove "a/" prefix
