"""Tests for pr_prompt package."""

from unittest.mock import MagicMock, patch

from pr_prompt.generator import PrPromptGenerator
from pr_prompt.markdown_builder import MarkdownBuilder
from pr_prompt.utils import FileFilter

from .conftest import create_mock_git_client


class TestFileFilter:
    """Test file filtering functionality."""

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


class TestMarkdownBuilder:
    """Test prompt building functionality."""

    def test_add_metadata_with_title_only(self, mock_git_client: MagicMock) -> None:
        """Test adding metadata with only title."""
        builder = MarkdownBuilder(mock_git_client)
        builder.add_metadata(
            include_commit_messages=False,
            pr_title="Fix bug in authentication",
            pr_description=None,
        )

        prompt = builder.build()
        assert "Fix bug in authentication" in prompt
        assert "**Title:**" in prompt

    def test_add_changed_files(self) -> None:
        """Test changed files display."""
        files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
        ]
        mock_git = create_mock_git_client(files=files)
        builder = MarkdownBuilder(mock_git)

        builder.add_changed_files(mock_git.get_diff_index())

        prompt = builder.build()
        assert "main.py" in prompt
        assert "utils.py" in prompt
        assert "test_main.py" in prompt
        assert "README.md" in prompt

    def test_add_context_file_with_syntax_highlighting(self) -> None:
        """Test context file with appropriate syntax highlighting."""
        mock_git = create_mock_git_client(files=["main.py", "example.py"])

        builder = MarkdownBuilder(mock_git)
        builder.add_context_files(["example.py"])

        prompt = builder.build()
        assert "context file content" in prompt


class TestPrPrompt:
    """Test PR prompt generator."""

    def test_default_initialization(self) -> None:
        """Test generator initializes with defaults."""
        generator = PrPromptGenerator()
        diff_context_lines = 999999
        default_include_commit_messages = True
        assert generator.diff_context_lines == diff_context_lines
        assert generator.include_commit_messages == default_include_commit_messages

    @patch("pr_prompt.generator.GitClient")
    def test_generate(
        self,
        mock_git_client_class: MagicMock,
    ) -> None:
        """Test prompt generation."""
        # Configure the mock to return our mock instance
        files = ["main.py", "uv.lock"]
        mock_git = create_mock_git_client(
            base_ref="origin/main",
            head_ref="feature/test",
            files=files,
            commit_messages=["Initial commit"],
        )
        mock_git_client_class.return_value = mock_git

        generator = PrPromptGenerator()
        prompt = generator.generate_review(
            base_ref="origin/main",
            head_ref="feature/test",
            pr_title="Test PR",
        )
        assert "Test PR" in prompt
        assert "main.py" in prompt
        assert "File diffs" in prompt
