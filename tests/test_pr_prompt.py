"""Tests for pr_prompt package."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pr_prompt.file_filters import FileFilter
from pr_prompt.generator import PrPromptGenerator
from pr_prompt.git_utils import GitClient, GitError
from pr_prompt.prompt_builder import PromptBuilder


class TestFileFilter:
    """Test file filtering functionality."""

    def test_exclude_no_patterns(self) -> None:
        """Test exclude with no patterns returns all files."""
        files = ["main.py", "test.py", "README.md"]
        assert FileFilter.exclude(files, []) == files

    def test_exclude_with_patterns(self) -> None:
        """Test exclude filters out matching patterns."""
        files = [
            "main.py",
            "test.py",
            "package-lock.json",
            "styles.min.css",
        ]
        patterns = ["*lock*", "*.min.*"]
        result = FileFilter.exclude(files, patterns)
        assert result == ["main.py", "test.py"]

    def test_match_no_patterns(self) -> None:
        """Test match with no patterns returns empty list."""
        files = ["main.py", "test.py"]
        assert FileFilter.match(files, []) == []

    def test_match_with_patterns(self) -> None:
        """Test match returns files matching patterns."""
        files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
        ]
        patterns = ["src/*.py", "*.md"]
        result = FileFilter.match(files, patterns)
        assert sorted(result) == [
            "README.md",
            "src/main.py",
            "src/utils.py",
        ]

    def test_exclude_files_with_spaces(self) -> None:
        """Test that files with spaces in names are excluded."""
        files = [
            "main.py",
            "test file.py",
            "another file.txt",
            "normal_file.py",
        ]
        patterns = ["* *"]  # Pattern to match files with spaces
        result = FileFilter.exclude(files, patterns)
        assert result == ["main.py", "normal_file.py"]


class TestPromptBuilder:
    """Test prompt building functionality."""

    def test_add_metadata_with_title_only(self) -> None:
        """Test adding metadata with only title."""
        builder = PromptBuilder()
        builder.add_metadata(
            target_branch="main",
            feature_branch="bugfix/authentication",
            commit_messages=[],
            pr_title="Fix bug in authentication",
            pr_description=None,
        )

        prompt = builder.build()
        assert "Fix bug in authentication" in prompt
        assert "**Title:**" in prompt

    def test_add_changed_files_single_directory(self) -> None:
        """Test changed files display for single directory."""
        builder = PromptBuilder()
        files = ["main.py", "utils.py", "config.py"]
        builder.add_changed_files(files)

        prompt = builder.build()
        assert "main.py" in prompt
        assert "utils.py" in prompt

    def test_add_changed_files_multiple_directories(self) -> None:
        """Test changed files grouped by directory."""
        builder = PromptBuilder()
        files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
        ]
        builder.add_changed_files(files)

        prompt = builder.build()
        assert "src/" in prompt
        assert "tests/" in prompt

    def test_add_context_file_with_syntax_highlighting(self) -> None:
        """Test context file with appropriate syntax highlighting."""
        builder = PromptBuilder()
        context_files = {"example.py": "def hello():\n    print('Hello')"}
        builder.add_context_files(context_files)

        prompt = builder.build()
        assert "example.py" in prompt
        assert "def hello():" in prompt


class TestGitClient:
    """Test git client functionality."""

    @patch("subprocess.run")
    def test_run_success(self, mock_run: MagicMock) -> None:
        """Test successful git command execution."""
        mock_run.return_value = MagicMock(stdout="output\n", stderr="", returncode=0)

        client = GitClient()
        result = client.run("status")

        assert result == "output"
        mock_run.assert_called_once_with(
            ["git", "status"], capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    def test_run_failure(self, mock_run: MagicMock) -> None:
        """Test git command failure raises GitError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git", "status"], stderr="error message"
        )

        client = GitClient()
        with pytest.raises(GitError) as exc_info:
            client.run("status")

        assert "Git command failed" in str(exc_info.value)

    @patch("subprocess.run")
    def test_get_changed_files(self, mock_run: MagicMock) -> None:
        """Test getting changed files."""
        mock_run.return_value = MagicMock(stdout="file1.py\nfile2.py\n", returncode=0)

        client = GitClient()
        files = client.get_changed_files("main", "feature")

        assert files == ["file1.py", "file2.py"]


class TestPRPromptGenerator:
    """Test PR prompt generator."""

    def test_default_initialization(self) -> None:
        """Test generator initializes with defaults."""
        generator = PrPromptGenerator()
        default_max_diff = 50000
        assert generator.max_diff_chars == default_max_diff

    @patch.object(GitClient, "fetch_branch")
    @patch.object(GitClient, "get_changed_files")
    @patch.object(GitClient, "get_diff")
    @patch.object(GitClient, "get_commit_messages")
    def test_generate_basic(
        self,
        mock_commit_messages: MagicMock,
        mock_diff: MagicMock,
        mock_files: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        """Test basic prompt generation."""
        mock_files.return_value = ["main.py", "test.py"]
        mock_diff.return_value = "diff content"
        mock_commit_messages.return_value = ["Initial commit"]

        generator = PrPromptGenerator()
        prompt = generator.generate(
            target_branch="origin/main",
            feature_branch="feature/test",
            pr_title="Test PR",
        )

        assert "Test PR" in prompt
        assert "main.py" in prompt
        assert "File diffs" in prompt

    @patch.object(GitClient, "fetch_branch")
    @patch.object(GitClient, "get_changed_files")
    @patch.object(GitClient, "get_diff")
    @patch.object(GitClient, "get_commit_messages")
    def test_generate_with_blacklist(
        self,
        mock_commit_messages: MagicMock,
        mock_diff: MagicMock,
        mock_files: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        """Test generation with blacklisted files."""
        mock_files.return_value = [
            "main.py",
            "package-lock.json",
            "test.py",
        ]
        mock_diff.return_value = """diff --git a/main.py b/main.py
index a8b605e888..f0b1ecbba9 100644
--- a/main.py
+++ b/main.py
@@ -1,426 +1,347 @@
-old content
+new content"""

        mock_commit_messages.return_value = ["Fix bug"]

        generator = PrPromptGenerator()
        prompt = generator.generate(
            target_branch="origin/main",
            feature_branch="feature_test",
            blacklist_patterns=["*lock.json"],
        )

        # All files should be listed
        assert "main.py" in prompt
        assert "package-lock.json" in prompt

        # But diff should exclude blacklisted files
        mock_diff.assert_called_once()

        assert "+new content" in prompt
